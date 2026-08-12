# Recreation Breakdown Schema

Use this schema for reference-video analysis and adapted brief creation.

## Reference Breakdown

```json
{
  "source": {
    "path_or_url": "",
    "duration_seconds": 12.4,
    "raw_target_duration_seconds": 12.4,
    "target_duration_seconds": 12,
    "duration_rounding_policy": "round half up to an integer; cap at 15 seconds; Seedance supports 4-15 seconds",
    "source_ratio": "9:16",
    "target_ratio": "9:16",
    "ratio": "9:16",
    "ratio_policy": "match the reference video aspect ratio by choosing the nearest Seedance-supported ratio",
    "width": 720,
    "height": 1280,
    "fps": 30,
    "platform_style": "TikTok | Douyin | Xiaohongshu | other",
    "content_type": "ecommerce demo | testimonial | skit | tutorial | before-after | other"
  },
  "analysis_assets": {
    "contact_sheet": "",
    "sampled_frames": [],
    "scene_candidate_frames": [],
    "audio_analysis": "",
    "extracted_audio": "",
    "audio_track_status": "present | absent | unknown",
    "ocr_status": "tool_generated | manually_read | inferred | unavailable",
    "transcript_status": "tool_generated | manually_transcribed | tool_generated_empty | unavailable | not_extracted"
  },
  "voiceover_layer": {
    "detected": true,
    "confidence": 0.86,
    "language": "zh",
    "backend": "faster-whisper | openai-whisper | whisper.cpp | manual | unavailable",
    "speaker_style": "young energetic male | warm female presenter | unknown",
    "segments": [
      {"start": 0.0, "end": 2.0, "text": "", "role": "hook"}
    ],
    "relationship_to_ocr": "matches_captions | differs_from_captions | captions_are_standalone_stickers | no_ocr | not_evaluated",
    "reason": "",
    "generation_rule": "preserve clear voiceover | do not force voiceover | unresolved; ask user or rerun ASR"
  },
  "voiceover_correction": {
    "policy": "Use ASR for timing and speech presence; use OCR/manual captions plus context for wording correction; never pass raw ASR directly to generation. Default adaptation is product_swap: preserve reference sentence structure, tone, rhythm, segment order, and timing, and only replace necessary product-specific information unless the user explicitly gives copy requirements.",
    "rewrite_mode": "product_swap | category_template_only_when_explicitly_requested",
    "needs_correction": false,
    "correction_source": "ocr_over_asr | manual_context | asr_context_normalized | unavailable",
    "reference_voiceover_corrected": [
      {"start": 0.0, "end": 2.0, "asr_text": "", "ocr_text": "", "corrected_text": "", "evidence": "ocr_over_asr"}
    ]
  },
  "voiceover_style_blueprint": {
    "speaker": "young energetic Mandarin commercial voice",
    "emotion": "excited, refreshing, bright, shareable, punchy",
    "pace": "fast but clear",
    "delivery": "short commercial punches with rising endings",
    "pause_style": "tiny pauses between slogan lines",
    "energy_curve": "strong hook -> sensory excitement -> product payoff -> CTA lift",
    "mix_rule": "voiceover in front of music and SFX",
    "avoid": ["flat narration", "slow explanation", "overly long sentences"]
  },
  "copywriting": {
    "spoken_transcript": [
      {"start": 0.0, "end": 2.0, "text": "", "role": "hook", "evidence": "audio | visual_caption | inferred"}
    ],
    "on_screen_text": [
      {"start": 0.0, "end": 2.0, "text": "", "visual_role": "hook sticker", "evidence_frame": ""}
    ],
    "formula": "",
    "hook": "",
    "pain_or_tension": "",
    "product_entry": "",
    "proof_or_demo": "",
    "cta": "",
    "tone": ""
  },
  "model_presence": {
    "presence_type": "none | presenter | lifestyle model | hand model | body-only model | multiple people | other",
    "shots": [
      {
        "start": 0.0,
        "end": 2.0,
        "framing": "full face | partial face | body only | hands only | back view | silhouette | product-only",
        "action": "",
        "relationship_to_product": "wearing | holding | demonstrating | reacting | background atmosphere | none",
        "identity_requirement": "none; preserve role and action only, not face identity"
      }
    ],
    "transfer_rule": "Preserve the same model/host role and action pattern with truthful anonymous adult model language unless unsafe or category-inappropriate."
  },
  "caption_style": {
    "placement": "top | center | lower third | sticker stack | subtitle band | none",
    "typography_style": "",
    "color_and_outline": "",
    "animation_or_timing": "",
    "density": "none | low | medium | high",
    "transfer_rule": "Preserve placement, rhythm, and visual weight. If the user gave no copy direction, only replace product-specific words and protected/unsupported content."
  },
  "sticker_overlay_style": {
    "corner_marks": "",
    "feature_badges": "",
    "checkmarks_or_icons": "",
    "arrows_or_callouts": "",
    "phone_frame_or_picture_in_picture": "",
    "pop_timing": "",
    "visual_weight": "subtle | medium | strong",
    "transfer_rule": "Preserve sticker type, placement, pop timing, and visual weight while replacing brand-specific marks and unsupported claims."
  },
  "sound_design": {
    "music_bed": "",
    "voiceover_energy": "",
    "transition_sfx": "",
    "sticker_pop_sfx": "",
    "product_handling_sfx": "",
    "proof_point_sfx": "",
    "cta_accent_sfx": "",
    "transfer_rule": "Preserve the reference video's sound-effect rhythm and proof-point accents without copying protected music or lyrics."
  },
  "scene_style": {
    "background": "",
    "lighting": "",
    "palette": "",
    "props": "",
    "wardrobe_or_human_styling": "",
    "surface_textures": "",
    "platform_visual_language": "",
    "transfer_rule": "Preserve the reference video's scene design unless the product category requires a visible adaptation."
  },
  "motion_style": {
    "camera_energy": "static | stabilized | handheld | fast social montage | slow premium commercial | other",
    "movement_sequence": ["push-in", "cut", "pan"],
    "transition_style": "",
    "speed_changes": "",
    "transfer_rule": "Match camera intent, direction, shot order, and movement energy."
  },
  "transfer_policy": {
    "preserve": [
      "model/host presence if present",
      "shot order and timing proportions",
      "framing and camera movement",
      "subject actions and product interactions",
      "scene design, lighting, palette, props",
      "caption placement and rhythm",
      "voiceover formula and CTA logic"
    ],
    "replace_or_remove": [
      "original product and brand assets",
      "watermarks and platform UI",
      "exact copied captions or protected scripts",
      "unsupported claims",
      "celebrity likeness or face identity requirements",
      "unsafe or sexualized elements"
    ]
  },
  "shots": [
    {
      "start": 0.0,
      "end": 2.5,
      "framing": "close-up | medium | wide | macro",
      "camera": "push-in | pull-back | handheld | pan | tilt | orbit | static",
      "subject": "",
      "action": "",
      "setting": "",
      "transition": "cut",
      "audio_cue": "",
      "visible_text": "",
      "model_or_host_role": "",
      "caption_style_note": "",
      "sticker_overlay_note": "",
      "sound_effect_note": "",
      "scene_style_note": "",
      "reference_element_to_preserve": "",
      "attention_job": "stop scroll | explain | prove | convert"
    }
  ],
  "rhythm": {
    "first_frame_tactic": "",
    "average_shot_seconds": 0,
    "cut_density": "low | medium | high",
    "music_or_sfx": "",
    "pace_notes": ""
  },
  "viral_mechanism": {
    "scroll_stop_reason": "",
    "retention_reason": "",
    "conversion_reason": "",
    "risks_to_avoid": []
  }
}
```

## Reference Storyboard

Create this before adaptation. It should describe the original reference video as faithfully as possible.

```json
{
  "reference_storyboard": [
    {
      "start": 0.0,
      "end": 2.5,
      "purpose": "",
      "visual": "",
      "model_or_host_role": "",
      "framing": "",
      "camera": "",
      "action": "",
      "scene_style": "",
      "caption_style": "",
      "sticker_overlay": "",
      "sound_effect": "",
      "voiceover_or_audio": "",
      "on_screen_text": "",
      "reference_element_to_preserve": ""
    }
  ]
}
```

## Adapted Seedance Brief

```json
{
  "product_name": "",
  "objective": "",
  "target_platform": "douyin",
  "ratio": "9:16",
  "ratio_policy": "follow source.target_ratio unless explicitly overridden",
  "duration": 12,
  "raw_reference_duration": 12.4,
  "duration_policy": "Round the raw reference duration half up to an integer; if reference duration is >15 seconds, cap output at 15 seconds; if rounded duration is <4 seconds, ask before padding because Seedance supports 4-15 seconds.",
  "voiceover_language": "zh-CN",
  "voiceover_policy": {
    "source_detected": true,
    "source_confidence": 0.86,
    "preserve_voiceover": true,
    "speaker_style": "young energetic male",
    "relationship_to_on_screen_text": "matches_captions",
    "generation_instruction": "If preserve_voiceover is true, audio must include clear Mandarin voiceover above music and sound effects. If preserve_voiceover is false, do not force spoken narration."
  },
  "caption_layer_policy": {
    "mode": "sparse_stickers",
    "available_modes": ["voiceover_only", "sparse_stickers", "caption_driven", "no_readable_text"],
    "relationship_to_voiceover": "matches_voiceover | differs_from_voiceover | standalone_stickers | no_voiceover | unknown",
    "allow_voiceover_subtitles": false,
    "rule": "Use only one readable text layer. If voiceover is preserved, do not also generate line-by-line transcript subtitles by default; keep only sparse stickers, punch headlines, feature badges, or CTA lockups unless caption_driven is explicitly selected."
  },
  "voiceover_style_blueprint": {
    "speaker": "",
    "emotion": "",
    "pace": "",
    "delivery": "",
    "pause_style": "",
    "energy_curve": "",
    "mix_rule": "",
    "avoid": []
  },
  "reference_logic_to_preserve": [
    "opening hook pattern",
    "shot rhythm",
    "demo payoff"
  ],
  "reference_fidelity_mode": "reference-faithful",
  "reference_elements_to_preserve": [
    "model/host presence if present",
    "shot count and shot order",
    "camera movement",
    "scene style",
    "caption style",
    "sticker and overlay style",
    "sound-effect rhythm",
    "voiceover rhythm"
  ],
  "required_replacements": [
    "replace the reference product with the user's product",
    "replace protected brand captions, original product words, and unsupported claims; preserve spoken sentence structure when no user copy direction is provided",
    "remove watermarks and platform UI",
    "remove unsupported claims"
  ],
  "product_identity_constraints": "",
  "user_supplied_facts": "",
  "adapted_voiceover": [
    {"start": 0.0, "end": 2.5, "text": ""}
  ],
  "reference_voiceover_corrected": [
    {"start": 0.0, "end": 2.5, "corrected_text": "", "evidence": "asr_context_normalized | ocr_over_asr | manual_context"}
  ],
  "adapted_on_screen_text": [
    {"start": 0.0, "end": 2.5, "text": "", "rendering_instruction": "sparse sticker/headline/CTA intent only when voiceover is preserved; not a line-by-line transcript subtitle unless caption_layer_policy.mode is caption_driven"}
  ],
  "shot_plan": [
    {
      "start": 0.0,
      "end": 2.5,
      "purpose": "hook",
      "visual": "",
      "model_or_host_role": "",
      "reference_element_preserved": "",
      "adaptation_reason": "",
      "scene_style": "",
      "sticker_overlay": "",
      "sound_effect": "",
      "framing": "",
      "camera": "",
      "action": "",
      "audio": ""
    }
  ],
  "negative_constraints": [
    "no watermark",
    "no copied captions",
    "no unsupported claims"
  ]
  ,
  "storyboard_input_policy": {
    "submit_storyboard_to_video_model": true,
    "storyboard_role": "director reference for shot logic, scene style, model/action blocking, overlays, captions, sound cues, and camera movement",
    "product_image_role": "identity reference for product shape, color, packaging, label layout, logo placement, materials, and accessories",
    "person_face_marker_rule": "If a visible face appears in the storyboard sheet, add a red 5x6 grid overlay only on the face area; final video must show a realistic anonymous adult face without the red grid.",
    "rejection_fallback": "If the video API rejects the storyboard image, regenerate a safer storyboard sheet before falling back to structured prompt plus product images."
  }
}
```

The `shot_plan` must total exactly integer `duration`, where `duration = round_half_up(min(reference duration, 15))`. The shot count should follow the reference-video structure. Merge, split, trim, or compress shots only when needed to fit the target duration, and record the adaptation reason.
