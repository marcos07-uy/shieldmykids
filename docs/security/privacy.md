# Privacy Principles

## Product Position

Shield My Kids is a parental-control product, not a surveillance product.

The product should collect the minimum data needed to:

- Calculate screen time.
- Enforce family rules.
- Show useful parent summaries.
- Debug agent health.
- Maintain audit history.

## Data The Product May Collect

MVP may collect:

- Parent email.
- Parent display name.
- Child display name.
- Child time zone.
- Device name.
- Device platform.
- Agent version.
- Device last-seen timestamp.
- Active usage intervals.
- Foreground app name or app identifier where available.
- Policy state.
- Enforcement status.
- Non-sensitive diagnostics.

## Data The Product Must Not Collect

Do not collect:

- Keystrokes.
- Screenshots.
- Camera images.
- Microphone audio.
- Passwords.
- Browser passwords.
- Private message contents.
- Email contents.
- Clipboard contents.
- Precise location, unless a future explicit product decision and privacy review adds it.

## Child Transparency

Child devices must show:

- The product is installed.
- The device is managed.
- Usage may be reported.
- Rules may be enforced.
- Current allowed/warned/blocked state.

The product must not include a hidden mode.

## Parent Dashboard Privacy

The dashboard should prioritize summaries:

- Total time by child.
- Total time by device.
- App usage categories where available.
- Recent enforcement events.

Avoid turning the dashboard into a content-monitoring surface.

## Data Retention

Suggested MVP retention:

- Raw usage events: 90 days.
- Aggregated usage: 1 year.
- Audit events: 1 year or longer if storage cost is acceptable.
- Pairing codes: expire within minutes.
- Device commands: expire after completion or a short TTL.
- Diagnostics: short retention, such as 14 to 30 days.

Retention should be configurable by environment.

## Data Minimization

Implementation should:

- Store hashes for credentials and pairing codes.
- Avoid collecting stable hardware identifiers unless necessary.
- Avoid collecting full window titles if they reveal private content.
- Prefer application identity over document/content identity.
- Avoid free-form diagnostics that could include private data.

## Parent Export And Deletion

Future capability:

- Export family data.
- Delete child profile.
- Revoke and delete device.
- Delete account data.

MVP should at least support internal deletion paths and avoid irreversible coupling.

