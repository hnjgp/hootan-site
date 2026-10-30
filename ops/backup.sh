#!/bin/sh
# Nightly pg_dump at 03:00 (TZ) into /backups, keeping 7 days.
# "backup.sh now" takes one dump and exits.
# Restore: pg_restore -h db -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists --no-owner --no-privileges <file>
set -eu

dump() {
	file="/backups/hootan_$(date +%Y-%m-%d_%H%M).dump"
	pg_dump -Fc -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$file.part"
	mv "$file.part" "$file"
	find /backups -name 'hootan_*.dump' -mtime +6 -delete
	echo "backup: $file $(du -h "$file" | cut -f1)"
}

if [ "${1:-}" = "now" ]; then
	dump
	exit 0
fi

while true; do
	next=$(date -d "03:00" +%s)
	[ "$next" -gt "$(date +%s)" ] || next=$(date -d "tomorrow 03:00" +%s)
	sleep $(( next - $(date +%s) ))
	dump || echo "backup: failed"
done
