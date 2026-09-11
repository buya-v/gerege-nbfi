#!/bin/bash
# OH-TIERD8-BW: the disposable copy was declared "already re-seeded to MNT and built", but the
# compiled test classes on disk were still EUR (CurrencyGlobalInitializerStep.class and friends
# contained the string EUR). The source files carry MNT. The build was therefore stale, so this
# targeted compile of only the two touched modules refreshes the classes; then it greps the class
# files to prove MNT and no standalone EUR constant. Verifiability: the grep is the proof.
set -uo pipefail
REPO=/Users/buv/fineract-tierd
OUT=/Users/buv/oh-gerege-tierd8/.softhouse/capture/tierd-feasibility/chargeoff-mnt
JVMARGS="-Xmx3g -XX:+UseSerialGC -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=128m -Xss1m --add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED --add-exports=java.naming/com.sun.jndi.ldap=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.security=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.management/javax.management=ALL-UNNAMED --add-opens=java.naming/javax.naming=ALL-UNNAMED --add-opens=java.rmi/sun.rmi.transport=null"
echo "=== compile start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
docker run --rm --name tierd-chargeoff-compile --network container:tierd-oracle-app \
  -u "$(id -u):$(id -g)" -v "$REPO":/work -v fineract-gradle-cache:/gradle-home -w /work \
  -e GRADLE_USER_HOME=/gradle-home -e HOME=/gradle-home \
  -e GRADLE_OPTS="-Dorg.gradle.internal.http.connectionTimeout=120000 -Dorg.gradle.internal.http.socketTimeout=120000 -Dorg.gradle.internal.repository.max.retries=8" \
  eclipse-temurin:21-jdk \
  ./gradlew --no-daemon --console=plain --max-workers=1 -Dorg.gradle.jvmargs="$JVMARGS" \
    :fineract-e2e-tests-core:compileTestJava :fineract-e2e-tests-runner:compileTestJava \
    -x spotlessCheck -x allureReport -x buildJavaSdk -x :fineract-client:buildJavaSdk -x :fineract-client-feign:buildJavaSdk -x :fineract-avro-schemas:buildJavaSdk
rc=$?
echo "=== compile end $(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc ==="
echo "=== class constant proof ==="
for c in \
 fineract-e2e-tests-runner/build/classes/java/test/org/apache/fineract/test/initializer/global/CurrencyGlobalInitializerStep.class \
 fineract-e2e-tests-runner/build/classes/java/test/org/apache/fineract/test/initializer/global/ChargeGlobalInitializerStep.class \
 fineract-e2e-tests-core/build/classes/java/test/org/apache/fineract/test/factory/LoanProductsRequestFactory.class ; do
  printf '%s: ' "$c"
  LC_ALL=C grep -a -o -E 'MNT|EUR' "$c" 2>/dev/null | sort | uniq -c | tr '\n' ' '
  echo
done
exit $rc
