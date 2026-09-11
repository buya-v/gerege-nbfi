#!/bin/bash
# OH-TIERD12-CE: replay LoanAccrualActivity-Part1.feature (all 50 accrual-activity scenarios)
# with the Feign capture on, in the JDK container over the DISPOSABLE copy, tenant `tierd`.
# Copy of accrual-activity-mnt/run-accrualactivity-mnt.sh (OH-TIERD11-CC), itself a copy of
# writeoff-mnt/run-writeoff-mnt.sh (OH-TIERD10-CA); only FEATURE, LOG and the container name
# changed, and the DB host is resolved from the running throwaway.
#
# The branch this capture is after is createJournalEntriesForAccruals
# [AccrualBasedAccountingProcessorForLoan.java:2015] (types accrual, accrualAdjustment,
# accrualActivity) -- the accrual postings.  The journal-entry LEGS are swept separately, by
# curl against this same throwaway, BEFORE teardown (step 3 of OH-TIERD12-CE).
set -uo pipefail
REPO=/Users/buv/fineract-tierd
FEATURE=src/test/resources/features/LoanAccrualActivity-Part1.feature
LOG=/work/fineract-e2e-tests-runner/build/capture/feign-accrual-activity-p1-mnt.log
DBHOST="${TESTDB_HOSTNAME:-$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' tierd-oracle-db)}"
JVMARGS="-Xmx3g -XX:+UseSerialGC -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=128m -Xss1m --add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED --add-exports=java.naming/com.sun.jndi.ldap=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.security=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.management/javax.management=ALL-UNNAMED --add-opens=java.naming/javax.naming=ALL-UNNAMED --add-opens=java.rmi/sun.rmi.transport=null"
echo "=== run start $(date -u +%Y-%m-%dT%H:%M:%SZ) DBHOST=$DBHOST ==="
docker run --rm \
  --name tierd-accrualactivity-p1-gradle \
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
  -e TESTDB_HOSTNAME="$DBHOST" \
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
rc=$?
echo "=== run end $(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc ==="
exit $rc
