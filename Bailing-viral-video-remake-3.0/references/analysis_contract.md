# Reference Video Analysis Contract

Use this contract to make the "reference video breakdown" complete before recreation.

## Required Layers

1. Metadata: duration, ratio, width, height, fps, audio presence.
2. Frames: evenly sampled frames plus scene-change candidate frames.
3. Shot structure: start/end time, framing, camera, subject, action, transition, visual emphasis.
4. On-screen text: OCR or manual reading with timestamp and role.
5. Spoken copy: transcript or evidence-based inferred voiceover intent.
6. Copywriting strategy: hook, pain point, product entry, proof, benefit, objection handling, CTA.
7. Rhythm: first-frame tactic, shot durations, cut density, music/SFX cues, pacing.
8. Viral mechanism: scroll-stop reason, retention reason, conversion reason.
9. Risks: claims, protected logos, copied text, unsafe or non-compliant elements to avoid.

## Evidence Rules

- Mark each text item as `tool_generated`, `manually_read`, or `inferred`.
- Do not treat inferred copy as an exact transcript.
- Do not copy protected brand slogans, watermarks, or platform text into the adapted video. If the user gave no copy direction or selling-point requirements, keep the reference spoken sentence structure and only replace product-specific information. Convert into a new product-specific structure only when the user explicitly asks for a different copy angle.
- Keep unsupported claims out of the adapted version unless the user supplies proof.

## Completion Bar

The breakdown is incomplete if it lacks any of:

- at least one hook observation
- at least one on-screen text observation or an explicit "none visible" note
- spoken transcript status
- shot timings
- product proof logic
- CTA logic
