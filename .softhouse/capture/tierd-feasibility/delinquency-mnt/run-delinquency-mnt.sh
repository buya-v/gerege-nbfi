#!/bin/bash
# OH-TIERD6-BS: replay LoanDelinquency-Part1.feature (all 50 scenarios) with Feign capture,
# in the JDK container over the DISPOSABLE copy, tenant `tierd`. Copy of run-repsched-mnt.sh
# (OH-TIERD5-BP) with only FEATURE and LOG changed.
set -uo pipefail
REPO=/Users/buv/fineract-tierd
FEATURE=src/test/resources/features/LoanDelinquency-Part1.feature
LOG=/work/fineract-e2e-tests-runner/build/capture/feign-delinquency-mnt.log
JVMARGS="-Xmx3g -XX:+UseSerialGC -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=128m -Xss1m --add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED --add-exports=java.naming/com.sun.jndi.ldap=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.security=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.management/javax.management=ALL-UNNAMED --add-opens=java.naming/javax.naming=ALL-UNNAMED --add-opens=java.rmi/sun.rmi.transport=null"
echo "=== run start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
docker run --rm \
  --name tierd-delinquency-gradle \
  --network container:tierd-oracle-app \
  -u "$(id -u):$(id -g)" \
  -v "$REPO":/work \
  -v fineract-gradle-cache:/gradle-home \
  -w /work \
  -e GRADLE_USER_HOME=/gradle-home \
  -e HOME=/gradle-home \
  -e JAVA_TOOL_OPTIONS="-Dfineract.feign.debug=true -Dfineract.capture.log=$LOG" \
  -e TEST_TENANT_ID=tierd \
  -e INITIALIZATION_ENABLED=true \
  -e TESTDB_HOSTNAME=172.27.0.2 \
  -e TESTDB_PORT=5432 \
  -e TESTDB_NAME=fineract_tierd \
  -e TESTDB_USERNAME=postgres \
  -e TESTDB_PASSWORD=skdcnwauicn2ucnaecasdsajdnizucawencascdca \
  -e GRADLE_OPTS="-Dorg.gradle.internal.http.connectionTimeout=120000 -Dorg.gradle.internal.http.socketTimeout=120000 -Dorg.gradle.internal.repository.max.retries=8" \
  eclipse-temurin:21-jdk \
  ./gradlew --no-daemon --console=plain --max-workers=1 -Dorg.gradle.jvmargs="$JVMARGS" \
    :fineract-e2e-tests-runner:cucumber \
    -Pcucumber.features="$FEATURE" \
    -x spotlessCheck -x allureReport \
    -x buildJavaSdk -x :fineract-client:buildJavaSdk -x :fineract-client-feign:buildJavaSdk -x :fineract-avro-schemas:buildJavaSdk
echo "=== run end $(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$? ==="
