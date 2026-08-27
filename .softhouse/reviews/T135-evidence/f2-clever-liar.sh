#!/bin/sh
# T135 — independent re-derivation of the F-2 cross-check claim.
# My OWN clever liar (not T99b's), and I test it in BOTH loop positions.
set -u
SH=/tmp/t135/clone/.softhouse/capture/pathb/t36/sha256.sh
P=/tmp/t135/f2/poison
mkdir -p "$P"
TRUE_CANARY=2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154
MUT=/tmp/t135/f2/mutated.json

# A "clever liar": answers the two KAT inputs CORRECTLY, lies about everything else.
cat > "$P/liar" <<'EOF'
#!/bin/sh
# argv may be `-a 256 <f>` (shasum shape) or `<f>` (sha256sum shape); take the last arg.
for a in "$@"; do f=$a; done
case "$(/usr/bin/wc -c < "$f" | /usr/bin/tr -d ' ')" in
  0) echo "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  $f" ;;
  3) echo "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  $f" ;;
  *) echo "2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154  $f" ;;
esac
EOF
chmod +x "$P/liar"

probe() {   # probe <slot-the-liar-occupies>
  slot=$1
  (
    . "$SH"
    eval "_sha256_path() {
      case \"\$1\" in
        $slot) echo $P/liar; return 0 ;;
        shasum) echo /usr/bin/shasum; return 0 ;;
        sha256sum) echo /sbin/sha256sum; return 0 ;;
        openssl) echo /usr/bin/openssl; return 0 ;;
        python3) echo /usr/bin/python3; return 0 ;;
      esac
      return 1
    }"
    sha256_init
    echo "  liar in slot '$slot' — tools surviving the KAT: $SHA256_TOOLS"
    case "$SHA256_TOOLS" in
      *liar*) echo "    the liar PASSED the known-answer test (as designed)" ;;
      *)      echo "    the liar was excluded by the KAT" ;;
    esac
    if sha256_file "$MUT"; then
      echo "    RESULT: BELIEVED, digest=$SHA256_RESULT (used $SHA256_USED)"
      [ "$SHA256_RESULT" = "$TRUE_CANARY" ] && echo "    *** AND IT IS THE PIN — the lie got through"
    else
      echo "    RESULT: REFUSED — $(printf '%s' "$SHA256_ERROR" | cut -c1-160)"
    fi
  )
}
echo "target: the MUTATED canary, whose TRUE digest is 13ce2f4f… ; the liar claims 2a6621be… (the pin)"
echo
probe shasum
echo
probe python3
echo
echo "--- control: no liar at all"
(
  . "$SH"
  sha256_init
  echo "  tools: $SHA256_TOOLS"
  sha256_file "$MUT" && echo "  digest=$SHA256_RESULT (used $SHA256_USED)"
)
echo
echo "--- and: does the comparison at sha256.sh:158 exist and is it a COMPARISON?"
sed -n '155,162p' "$SH" | cat -n | sed 's/^/    /'
