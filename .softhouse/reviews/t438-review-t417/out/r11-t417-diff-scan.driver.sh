T=/tmp/t438/t417tree/.softhouse/capture/t417-scheduler-attribution
echo "=== float/double/decimal literals in T417 shell+sql:"
grep -rnE '\bfloat\b|\bdouble\b|[0-9]+\.[0-9]+e|::float|::double|::numeric' $T --include=*.sh --include=*.sql || echo "  none"
echo "=== write verbs against the oracle in T417 shell+sql:"
grep -rniE '\b(INSERT +INTO|UPDATE +[a-z_]+ +SET|DELETE +FROM|TRUNCATE|ALTER +TABLE|DROP +TABLE|CREATE +TABLE|GRANT|COPY .* FROM)\b' $T --include=*.sh --include=*.sql || echo "  none"
echo "=== prohibited engines / vendors:"
grep -rniE 'mysql|mariadb|ojdbc|oracle\.jdbc|1521|stripe|plaid|lithic|persona' $T --include=*.sh --include=*.sql || echo "  none"
echo "=== deposit/insured language:"
grep -rniE 'insured|guaranteed|protected deposit|deposit insurance' $T --include=*.sh --include=*.sql || echo "  none"
echo "=== hard-coded tz offsets:"
grep -rnE '\+08:00|\+07:00|UTC\+8|GMT\+8' $T --include=*.sh --include=*.sql || echo "  none"
echo "=== capsql.sh write refusal:"
sed -n '1,36p' $T/capsql.sh
