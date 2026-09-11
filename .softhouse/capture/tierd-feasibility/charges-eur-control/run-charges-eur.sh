#!/bin/bash
# OH-CHGCTL-BV: replay THREE failing scenarios of LoanChargesInstallmentFee.feature with Feign
# FULL capture, in the JDK container over the DISPOSABLE copy, tenant `tierd`, on the copy with
# the five currency constants reverted to EUR. Derived from
# ../uc10-eur-control/run-uc10-eur.sh (OH-UC10CTL-BQ), itself derived from
# ../repayment-schedule-mnt/run-repsched-mnt.sh (OH-TIERD5-BP): same image, same JVM args, same
# capture env, same excluded SDK tasks. Only the feature selector (a name filter selecting the
# three scenarios), log name, container name and the DB host (resolved from the running
# throwaway instead of a hard-coded IP) differ.
set -uo pipefail
REPO=/Users/buv/fineract-tierd
FEATURE=src/test/resources/features/LoanChargesInstallmentFee.feature
# Scenario 26 (C3890, cumulative-loan 100-minor-unit period-2 split) +
# scenario 4 (C3786, percent-interest, one-minor-unit fee) +
# scenario 7 (C3788, all-charges, one-minor-unit fee). Anchored so scenario 17 ("Verify add
# installment fee charge: percentage ...") and scenario 27 ("Progressive loan - Verify final
# income accrual ...") do NOT match.
NAME='^Progressive loan - Verify the loan creation with installment fee charge: percentage interest charge type, interestRecalculation = false$|^Progressive loan - Verify the loan creation with installment fee charge: all charge types, interestRecalculation = false$|^Cumulative loan - Verify final income accrual with multiple fee charges created successfully$'
LOG=/work/fineract-e2e-tests-runner/build/capture/feign-installmentfee-eur.log
DBHOST="${TESTDB_HOSTNAME:-$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' tierd-oracle-db)}"
JVMARGS="-Xmx3g -XX:+UseSerialGC -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=128m -Xss1m --add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED --add-exports=java.naming/com.sun.jndi.ldap=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.security=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.management/javax.management=ALL-UNNAMED --add-opens=java.naming/javax.naming=ALL-UNNAMED --add-opens=java.rmi/sun.rmi.transport=null"
echo "=== run start $(date -u +%Y-%m-%dT%H:%M:%SZ) DBHOST=$DBHOST ==="
echo "NAME=$NAME"
docker run --rm \
  --name tierd-charges-eur-gradle \
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
    -Pcucumber.name="$NAME" \
    -x spotlessCheck -x allureReport \
    -x buildJavaSdk -x :fineract-client:buildJavaSdk -x :fineract-client-feign:buildJavaSdk -x :fineract-avro-schemas:buildJavaSdk
rc=$?
echo "=== run end $(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc ==="
exit $rc
