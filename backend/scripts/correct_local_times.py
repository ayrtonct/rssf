"""Correct only explicitly audited UTC rows to Sao Luis. Dry-run by default.

Manifest: [{"id":4017,"sensor_id":8900,"gateway_id":"gateway_lab_01",
            "data_hora":"2026-11-06 15:12:48"}]
Use --apply --backup /safe/path/unique-backup.json after inspecting the dry run.
Stop the old UTC writer before taking the final manifest and deploying the local writer.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mysql.connector
from config import DB_CONFIG


def correction(entry, current):
    before = datetime.fromisoformat(entry['data_hora'])
    if before.tzinfo is not None:
        raise ValueError('Manifest data_hora must be the exact naive database DATETIME')
    after = before - timedelta(hours=3)
    if (current['sensor_id'], current['gateway_id']) != (entry['sensor_id'], entry['gateway_id']):
        raise ValueError(f"Identity changed for id={entry['id']}")
    if current['data_hora'] == after:
        return None  # Same manifest can safely be retried.
    if current['data_hora'] != before:
        raise ValueError(f"Timestamp differs from audited value for id={entry['id']}")
    return after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    entries = json.loads(args.manifest.read_text())
    if not isinstance(entries, list) or not entries:
        parser.error('Manifest must be a nonempty list of audited records')
    if len({e['id'] for e in entries}) != len(entries):
        parser.error('Duplicate IDs in manifest')
    if args.apply and not args.backup:
        parser.error('--apply requires --backup (a new file, never overwritten)')
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SHOW COLUMNS FROM medicoes LIKE 'data_hora'")
        column = cursor.fetchone()
        if not column or not column['Type'].lower().startswith('datetime'):
            raise ValueError('This correction is exclusively for the audited DATETIME schema')
        conn.rollback()
        conn.start_transaction(readonly=not args.apply)
        snapshots, changes = [], []
        for entry in entries:
            cursor.execute('SELECT * FROM medicoes WHERE id = %s' + (' FOR UPDATE' if args.apply else ''), (entry['id'],))
            current = cursor.fetchone()
            if current is None:
                raise ValueError(f"Missing id={entry['id']}")
            target = correction(entry, current)
            snapshots.append(current)
            if target is not None:
                changes.append((target, entry['id'], current['data_hora']))
        print(json.dumps({'audited': len(entries), 'to_change': len(changes),
                          'changes': [{'id': row[1], 'before': row[2], 'after': row[0]} for row in changes]},
                         default=str, indent=2))
        if args.apply:
            # Exclusive file creation prevents accidental loss of the original snapshot.
            with args.backup.open('x') as handle:
                json.dump(snapshots, handle, default=str, indent=2)
                handle.flush()
                import os
                os.fsync(handle.fileno())
            for target, row_id, before in changes:
                cursor.execute('UPDATE medicoes SET data_hora = %s WHERE id = %s AND data_hora = %s',
                               (target, row_id, before))
                if cursor.rowcount != 1:
                    raise ValueError(f'Concurrent change for id={row_id}')
            conn.commit()
            print('Committed; original rows saved in backup.')
        else:
            conn.rollback()
            print('Dry run only; no rows changed.')
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
