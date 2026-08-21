#!/usr/bin/env bash
# Build the Fineract REFERENCE ORACLE image (fineract:latest) from the pinned
# source checkout, using a JDK 21 container (the host has no JVM).
#
# PostgreSQL is the only database in this program; this script builds only the
# application image — the DB comes from the postgresql compose profile.
set -euo pipefail

FINERACT_SRC="${FINERACT_SRC:-/Users/buv/fineract}"
CACHE_VOL="fineract-gradle-cache"
JDK_IMAGE="eclipse-temurin:21-jdk"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"

echo "=== reference-oracle image build ==="
echo "src        : ${FINERACT_SRC}"
echo "pinned     : $(git -C "${FINERACT_SRC}" rev-parse HEAD)"
echo "jdk image  : ${JDK_IMAGE}"

# Gradle cache volume, writable by the host uid we build as.
docker volume create "${CACHE_VOL}" >/dev/null
docker run --rm -v "${CACHE_VOL}:/gradle-home" alpine:3 \
  chown -R "${HOST_UID}:${HOST_GID}" /gradle-home

echo "=== step 1/2: gradle :fineract-provider:bootJar (tests skipped) ==="
# Maven Central intermittently terminates TLS handshakes when Gradle opens many
# parallel connections, which killed attempt 1. Throttle workers, lengthen the
# HTTP timeouts, and retry — the dependency cache is persistent, so each attempt
# resumes where the last one got to.
GRADLE_OPTS_HTTP="-Dorg.gradle.internal.http.connectionTimeout=120000 \
-Dorg.gradle.internal.http.socketTimeout=120000 \
-Dorg.gradle.internal.repository.max.retries=8 \
-Dorg.gradle.internal.repository.initial.backoff=1000"

BUILD_OK=0
for attempt in 1 2 3; do
  echo "--- bootJar attempt ${attempt}/3 ---"
  if docker run --rm \
      -u "${HOST_UID}:${HOST_GID}" \
      -v "${FINERACT_SRC}:/src" \
      -v "${CACHE_VOL}:/gradle-home" \
      -w /src \
      -e GRADLE_USER_HOME=/gradle-home \
      -e GRADLE_OPTS="${GRADLE_OPTS_HTTP}" \
      "${JDK_IMAGE}" \
      ./gradlew :fineract-provider:bootJar -x test \
        --no-daemon --console=plain --max-workers=2; then
    BUILD_OK=1
    break
  fi
  echo "--- attempt ${attempt} failed; retrying against the warm cache ---"
done
[ "${BUILD_OK}" = "1" ] || { echo "FATAL: bootJar failed after 3 attempts"; exit 1; }

JAR="$(ls -1 "${FINERACT_SRC}"/fineract-provider/build/libs/fineract-provider-*.jar \
       | LC_ALL=C grep -av -- '-plain\.jar$' | head -1)"
echo "bootJar    : ${JAR}"
[ -s "${JAR}" ] || { echo "FATAL: bootJar not produced"; exit 1; }

echo "=== step 2/2: docker build fineract:latest ==="
# Mirrors the jib container config in fineract-provider/build.gradle:314-344
# (base azul/zulu-openjdk-alpine:21, /app workdir, UTC, ports 8080/8443).
BUILD_CTX="$(mktemp -d)"
cp "${JAR}" "${BUILD_CTX}/fineract-provider.jar"
cat > "${BUILD_CTX}/Dockerfile" <<'DOCKERFILE'
FROM azul/zulu-openjdk-alpine:21
RUN apk add --no-cache busybox-extras curl || true
WORKDIR /app
COPY fineract-provider.jar /app/fineract-provider.jar
RUN mkdir -p /app/plugins /var/logs/fineract && chmod -R 777 /var/logs/fineract
EXPOSE 8080 8443
ENTRYPOINT ["java", \
  "-Duser.home=/tmp", \
  "-Dfile.encoding=UTF-8", \
  "-Duser.timezone=UTC", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar","/app/fineract-provider.jar"]
DOCKERFILE
docker build -t fineract:latest "${BUILD_CTX}"
rm -rf "${BUILD_CTX}"

echo "=== done: fineract:latest built ==="
docker images fineract:latest
