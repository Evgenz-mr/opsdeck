# Certificate Center

Certificate Center combines read-only TLS inspection with allowlisted renewal actions.

Thresholds:

- healthy: 30+ days;
- warning: 10-29 days;
- critical: less than 10 days.

Renewal stays an explicit action. Automatic renewal is intentionally disabled in the first release.

Recommended flow:

1. inspect certificate;
2. run `update-certificate` on selected target;
3. verify certificate again;
4. verify service health;
5. store result in audit history.
