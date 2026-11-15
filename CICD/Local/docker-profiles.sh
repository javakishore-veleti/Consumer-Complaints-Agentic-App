#!/usr/bin/env bash
# Shared helpers for lite local container profiles (D78).
# Sourced by docker-all-up.sh / docker-all-down.sh / docker-all-status.sh.

_CCA_PROFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_CCA_PROFILES_MAP="${_CCA_PROFILES_DIR}/profiles.map"

cca_list_all_services() {
  local f
  for f in "${_CCA_PROFILES_DIR}"/*/docker-compose.y*ml; do
    [ -e "$f" ] || continue
    basename "$(dirname "$f")"
  done
}

cca_known_profiles() {
  local line
  [ -f "$_CCA_PROFILES_MAP" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) continue ;;
    esac
    printf '%s\n' "${line%%=*}"
  done < "$_CCA_PROFILES_MAP"
}

# Prints one service name per line for the given profile.
cca_profile_services() {
  local profile="$1" line key val
  [ -n "$profile" ] || return 1
  [ -f "$_CCA_PROFILES_MAP" ] || {
    echo "missing profiles map: $_CCA_PROFILES_MAP" >&2
    return 1
  }
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) continue ;;
    esac
    key="${line%%=*}"
    val="${line#*=}"
    if [ "$key" = "$profile" ]; then
      # shellcheck disable=SC2086
      printf '%s\n' $val
      return 0
    fi
  done < "$_CCA_PROFILES_MAP"
  echo "unknown profile: $profile (known: $(cca_known_profiles | paste -sd' ' -))" >&2
  return 1
}

# Sets:
#   CCA_PROFILE   — empty or profile name
#   CCA_WIPE      — 0 or 1
#   CCA_SVC_ARGS  — remaining positional service names (array)
cca_parse_profile_args() {
  CCA_PROFILE=""
  CCA_WIPE=0
  CCA_SVC_ARGS=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --profile)
        shift
        [ -n "${1:-}" ] || {
          echo "usage: --profile <sqlite|postgres|mongodb>" >&2
          return 1
        }
        CCA_PROFILE="$1"
        shift
        ;;
      --profile=*)
        CCA_PROFILE="${1#--profile=}"
        [ -n "$CCA_PROFILE" ] || {
          echo "usage: --profile <sqlite|postgres|mongodb>" >&2
          return 1
        }
        shift
        ;;
      --wipe)
        CCA_WIPE=1
        shift
        ;;
      -*)
        echo "unknown option: $1" >&2
        return 1
        ;;
      *)
        CCA_SVC_ARGS+=("$1")
        shift
        ;;
    esac
  done
  if [ -n "$CCA_PROFILE" ] && [ "${#CCA_SVC_ARGS[@]}" -gt 0 ]; then
    echo "use either --profile or explicit service names, not both" >&2
    return 1
  fi
  if [ -n "$CCA_PROFILE" ]; then
    cca_profile_services "$CCA_PROFILE" >/dev/null || return 1
  fi
  return 0
}

# Echo service names for the current parse (one per line).
cca_resolved_services() {
  if [ -n "${CCA_PROFILE:-}" ]; then
    cca_profile_services "$CCA_PROFILE"
    return
  fi
  if [ "${#CCA_SVC_ARGS[@]}" -gt 0 ]; then
    printf '%s\n' "${CCA_SVC_ARGS[@]}"
    return
  fi
  cca_list_all_services
}
