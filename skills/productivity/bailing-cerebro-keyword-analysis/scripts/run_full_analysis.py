#!/usr/bin/env python3
"""
Amazon Cerebro Keyword Full Analysis (V3 + V4.1 Dynamic Attribute Discovery)

Core innovation: Instead of loading a fixed attribute tree, this script:
1. Analyzes keyword frequency to discover the product category
2. Builds a dynamic attribute tree from the data itself
3. Applies the 11-dimension Cosmo framework with data-driven patterns

Usage:
    python run_full_analysis.py --xlsx-path <path> [--asin <ASIN>]
"""
import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict

import openpyxl

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def safe_int(val):
    if val is None or val == '' or val == '-':
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def safe_float(val):
    if val is None or val == '' or val == '-':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def tokenize(kw):
    return re.findall(r'[a-z0-9]+', (kw or '').lower())


# ═══════════════════════════════════════════════════════════════
# Generic seed dictionary (cross-category, not product-specific)
# ═══════════════════════════════════════════════════════════════

GENERIC_SEED = {
    'AUDIENCE_FAMILY': {
        'women_universal': ['for women', "women's", 'for her', 'her skin', 'older women'],
        'men_universal': ['for men', "men's", 'for him', 'his skin'],
        'mature_50plus': ['mature', 'over 50', '50+', 'senior', 'over 60'],
        'youth_universal': ['young', 'youth', 'teen', 'adult', '20s'],
        'sensitive_skin': ['sensitive', 'gentle'],
        'dry_skin': ['dry skin', 'dry'],
        'oily_skin': ['oily', 'acne'],
        'post_pregnancy': ['mommy', 'pregnancy', 'postpartum'],
    },
    'MODIFIER_FAMILY': {
        'natural_origin': ['natural', 'organic', 'plant based', 'botanical', 'pure'],
        'clean_beauty': ['clean', 'non toxic', 'free from'],
        'cruelty_free': ['cruelty free', 'vegan'],
        'professional_grade': ['professional', 'clinical', 'medical grade', 'dermatologist'],
        'brand_legacy': ['luxury', 'premium', 'high end', 'classic', 'heritage'],
        'mass_market': ['drugstore', 'affordable', 'cheap', 'value'],
        'instant_results': ['instant', 'immediate', 'fast', 'quick'],
        'long_term_results': ['overnight', 'daily', 'long term'],
        'korean_beauty': ['korean', 'k beauty'],
        'japanese_beauty': ['japanese', 'j beauty'],
        'fragrance_free': ['fragrance free', 'unscented'],
        'spf': ['spf', 'sunscreen'],
    },
    'PURCHASE_CONTEXT': {
        'gift_packaging': ['gift', 'present', 'box'],
        'travel_size': ['travel', 'mini', 'sample'],
        'bulk_size': ['bulk', 'value size', 'family size', '8 oz', '16 oz'],
        'subscribe_save': ['subscribe', 'subscription'],
        'auto_delivery': ['auto', 'refill'],
    },
    'TEMPORAL': {
        'fourth_quarter': ['holiday', 'christmas', 'new year', 'thanksgiving', 'black friday'],
        'summer_specific': ['summer', 'vacation', 'beach'],
        'wedding_event': ['wedding', 'bride', 'prom', 'formal'],
    },
    'ORIGIN': {
        'korean': ['korean', 'k-beauty'],
        'japanese': ['japanese', 'j-beauty'],
        'european': ['european', 'french', 'italian', 'german'],
        'american': ['american', 'usa made'],
        'australian': ['australian'],
    },
    'GENERIC': {
        'healthcare_provider': ['medical', 'physician', 'dermatologist'],
        'professional_use': ['salon', 'spa', 'esthetician'],
        'review_keyword': ['review', 'reviews', 'comments'],
        'comparison_keyword': ['vs', 'comparison', 'versus', 'alternative'],
        'how_to': ['how to', 'tutorial', 'method'],
    },
}

# Heuristic word-type detectors (for dynamic attribute discovery)
# These are GENERAL patterns, not product-specific
FORM_HINTS = {'holder', 'case', 'stand', 'sticker', 'cover', 'skin', 'skins', 'wand',
              'card', 'reader', 'tape', 'strip', 'patch', 'mask', 'cream', 'gel',
              'lotion', 'serum', 'oil', 'stick', 'spray', 'roller', 'device',
              'machine', 'kit', 'set', 'bundle', 'pen', 'tube', 'jar', 'pump'}
BENEFIT_HINTS = {'firming', 'lifting', 'tightening', 'anti', 'aging', 'smoothing',
                 'brightening', 'moisturizing', 'hydrating', 'protect', 'defense',
                 'tap', 'pay', 'contactless', 'nfc', 'wireless', 'portable',
                 'rechargeable', 'waterproof', 'magnetic', 'adjustable'}
PAIN_HINTS = {'wrinkle', 'wrinkles', 'sag', 'sagging', 'loose', 'crepe', 'dry',
              'flaky', 'aged', 'dark spot', 'acne', 'damage', 'broken', 'lost',
              'lost', 'scratch', 'crack', 'fade', 'peel'}
AREA_HINTS = {'neck', 'face', 'facial', 'eye', 'body', 'chest', 'hand', 'hands',
              'arm', 'leg', 'stomach', 'belly', 'phone', 'card', 'wallet', 'pocket',
              'car', 'desk', 'table', 'wall', 'door', 'kitchen', 'bathroom'}
INGREDIENT_HINTS = {'collagen', 'retinol', 'vitamin', 'niacinamide', 'peptide',
                    'gold', 'silver', 'copper', 'zinc', 'silicone', 'plastic',
                    'leather', 'metal', 'wood', 'bamboo', 'carbon', 'titanium',
                    'aluminum', 'rubber', 'glass', 'ceramic'}
AUDIENCE_HINTS = {'women', 'men', 'kids', 'baby', 'girl', 'boy', 'senior',
                  'adult', 'teen', 'student', 'professional', 'traveler'}

BRAND_LIBRARY = {
    'dr', 'melaxin', 'cerave', 'loreal', 'estee', 'lauder',
    'olay', 'roc', 'gold', 'bond', 'nivea', 'jergens', 'weleda',
    'cetaphil', 'eucerin', 'aveeno', 'froya', 'meditherapy', 'gopure',
    'drmtlgy', 'elemis', 'eqqualberry', 'carotone', 'noor', 'wonder',
    'dekliderm', 'clarins', 'lancome', 'beeauro', 'ceoerty',
    'softanas', 'olavita', 'hyggear', 'balaayah', 'vitala', 'circadia',
    'strivectin', 'perbelle', 'medicube', 'shiseido', 'holipaw',
}


# ═══════════════════════════════════════════════════════════════
# Dynamic Attribute Discovery
# ═══════════════════════════════════════════════════════════════

def discover_attributes(keywords):
    """
    Analyze keyword data to dynamically build an 11-dimension attribute tree.

    Returns: dict matching the Cosmo attribute tree structure
    {DIM_NAME: {TAG_NAME: [pattern1, pattern2, ...]}}
    """
    # Step 1: Token frequency analysis
    token_freq = Counter()
    token_kw_count = defaultdict(set)  # token -> set of keywords containing it

    for kw in keywords:
        if not kw or kw == '-':
            continue
        tokens = tokenize(kw)
        for t in set(tokens):  # unique tokens per keyword
            token_freq[t] += 1
            token_kw_count[t].add(kw)

    # Step 2: Identify core words (appear in >=5 different keywords, top frequency)
    core_words = set()
    for token, freq in token_freq.most_common(30):
        if len(token_kw_count[token]) >= 5:
            core_words.add(token)

    # Step 3: Build dynamic attribute tree
    # Start with generic seed (cross-category)
    tree = {}
    for dim, tags in GENERIC_SEED.items():
        tree[dim] = {tag: list(patterns) for tag, patterns in tags.items()}

    # Ensure all 11 dimensions exist
    ALL_DIMS = [
        'INGREDIENT_FAMILY', 'PAIN_SPECIFIC', 'FORM_FAMILY', 'AREA_FAMILY',
        'AUDIENCE_FAMILY', 'MODIFIER_FAMILY', 'BENEFIT_FAMILY',
        'PURCHASE_CONTEXT', 'TEMPORAL', 'ORIGIN', 'GENERIC'
    ]
    for dim in ALL_DIMS:
        if dim not in tree:
            tree[dim] = {}

    # Step 4: Discover product-specific attributes
    # For each non-core high-frequency token, try to map to a dimension
    discovered = defaultdict(lambda: defaultdict(list))

    for token, freq in token_freq.most_common(100):
        if token in core_words:
            continue
        if freq < 3:
            continue
        if len(token) <= 1:
            continue

        # Skip common English stop words
        if token in {'for', 'the', 'and', 'with', 'to', 'of', 'in', 'on', 'a',
                      'is', 'it', 'your', 'you', 'are', 'be', 'or', 'at', 'by',
                      'from', 'as', 'an', 'this', 'that', 'all', 'not', 'but',
                      'can', 'will', 'has', 'have', 'had', 'do', 'does', 'did',
                      'my', 'me', 'we', 'they', 'he', 'she', 'us', 'them',
                      'up', 'out', 'so', 'no', 'yes', 'if', 'then', 'than',
                      'more', 'most', 'some', 'any', 'each', 'every', 'both',
                      'into', 'over', 'under', 'after', 'before', 'about',
                      'just', 'only', 'also', 'very', 'too', 'well',
                      'new', 'best', 'top', 'pro', 'max', 'plus', 'ultra',
                      'super', 'one', 'two', 'three', 'set', 'pack'}:
            # But some of these might be modifier tags
            if token in {'new', 'best', 'pro', 'max', 'plus', 'ultra', 'super'}:
                tag = f'discovered_{token}'
                discovered['MODIFIER_FAMILY'][tag].append(token)
            continue

        # Map to dimensions using hints
        if token in FORM_HINTS:
            tag = f'form_{token}'
            discovered['FORM_FAMILY'][tag].append(token)
        elif token in BENEFIT_HINTS:
            tag = f'benefit_{token}'
            discovered['BENEFIT_FAMILY'][tag].append(token)
        elif token in PAIN_HINTS:
            tag = f'pain_{token}'
            discovered['PAIN_SPECIFIC'][tag].append(token)
        elif token in AREA_HINTS:
            tag = f'area_{token}'
            discovered['AREA_FAMILY'][tag].append(token)
        elif token in INGREDIENT_HINTS:
            tag = f'ingredient_{token}'
            discovered['INGREDIENT_FAMILY'][tag].append(token)
        elif token in AUDIENCE_HINTS:
            tag = f'audience_{token}'
            discovered['AUDIENCE_FAMILY'][tag].append(token)
        else:
            # For unmapped high-freq tokens, use co-occurrence with core words
            # to infer the dimension. Default to GENERIC for safety.
            # If it co-occurs with form words, likely a form attribute
            co_tokens = set()
            for kw in list(token_kw_count[token])[:20]:
                co_tokens.update(tokenize(kw))

            if co_tokens & INGREDIENT_HINTS:
                tag = f'discovered_{token}'
                discovered['INGREDIENT_FAMILY'][tag].append(token)
            elif co_tokens & FORM_HINTS:
                tag = f'discovered_{token}'
                discovered['FORM_FAMILY'][tag].append(token)
            elif co_tokens & BENEFIT_HINTS:
                tag = f'discovered_{token}'
                discovered['BENEFIT_FAMILY'][tag].append(token)
            elif co_tokens & AREA_HINTS:
                tag = f'discovered_{token}'
                discovered['AREA_FAMILY'][tag].append(token)
            # If still unmapped and freq >= 10, put in GENERIC
            elif freq >= 10:
                tag = f'discovered_{token}'
                discovered['GENERIC'][tag].append(token)

    # Step 5: Also detect multi-word phrases (bigrams)
    bigram_freq = Counter()
    for kw in keywords:
        if not kw or kw == '-':
            continue
        tokens = tokenize(kw)
        for i in range(len(tokens) - 1):
            bigram = f'{tokens[i]} {tokens[i+1]}'
            bigram_freq[bigram] += 1

    for bigram, freq in bigram_freq.most_common(50):
        if freq < 5:
            continue
        # Check if any word in bigram is a core word
        bg_tokens = set(bigram.split())
        if bg_tokens & core_words:
            continue
        # Try to map bigram to dimension
        if any(t in INGREDIENT_HINTS for t in bg_tokens):
            tag = f'discovered_{bigram.replace(" ", "_")}'
            if tag not in tree['INGREDIENT_FAMILY']:
                discovered['INGREDIENT_FAMILY'][tag].append(bigram)
        elif any(t in FORM_HINTS for t in bg_tokens):
            tag = f'discovered_{bigram.replace(" ", "_")}'
            if tag not in tree['FORM_FAMILY']:
                discovered['FORM_FAMILY'][tag].append(bigram)
        elif any(t in BENEFIT_HINTS for t in bg_tokens):
            tag = f'discovered_{bigram.replace(" ", "_")}'
            if tag not in tree['BENEFIT_FAMILY']:
                discovered['BENEFIT_FAMILY'][tag].append(bigram)

    # Merge discovered into tree
    for dim, tags in discovered.items():
        for tag, patterns in tags.items():
            if tag not in tree[dim]:
                tree[dim][tag] = patterns

    return tree, core_words, token_freq


# ═══════════════════════════════════════════════════════════════
# Tagging (same as before but with dynamic tree)
# ═══════════════════════════════════════════════════════════════

def tag_keyword(kw, tree):
    k_norm = (kw or '').lower().strip()
    k_tokens = set(tokenize(kw))
    out = {}
    for dim_name, dim_tags in tree.items():
        tag_set = set()
        for tag_name, patterns in dim_tags.items():
            for p in patterns:
                if ' ' in p or '-' in p:
                    if p in k_norm:
                        tag_set.add(tag_name)
                        break
                else:
                    if p in k_tokens:
                        tag_set.add(tag_name)
                        break
        if tag_set:
            out[dim_name] = sorted(tag_set)
    return out


# ═══════════════════════════════════════════════════════════════
# V3 + V4.1 (unchanged from before)
# ═══════════════════════════════════════════════════════════════

def decompose_keyword(kw, core_words):
    if not kw or kw == '-':
        return '', '', '', ''
    words = tokenize(kw)
    core_parts, upper_parts, attr_parts, weak_parts = [], [], [], []
    for w in words:
        if w in core_words or any(c in w for c in ['cream', 'firm', 'neck', 'skin', 'wrink', 'collagen']):
            core_parts.append(w)
        elif w in UPPER_WORDS_HINT:
            upper_parts.append(w)
        elif w in BRAND_LIBRARY:
            weak_parts.append(w)
        else:
            attr_parts.append(w)
    return (' '.join(core_parts) if core_parts else '',
            ' '.join(upper_parts) if upper_parts else '',
            ' '.join(attr_parts) if attr_parts else '',
            ' '.join(weak_parts) if weak_parts else '')

UPPER_WORDS_HINT = {'women', 'womens', 'woman', 'men', 'mens', 'girls', 'boys',
                    'kids', 'baby', 'adult', 'senior', 'female', 'male'}

def traffic_tier(vol):
    if vol >= 5000: return '大词'
    if vol >= 1000: return '中词'
    return '小词'

def v3_classify(vol, iq, organic_rank, weak_words, kw):
    kw_lower = (kw or '').lower()
    if weak_words:
        return 'C'
    kw_tokens = set(tokenize(kw_lower))
    if kw_tokens & BRAND_LIBRARY:
        return 'C'
    if vol == 0: return 'D'
    if vol >= 5000 and iq >= 1000 and (organic_rank == 0 or organic_rank > 10): return 'S'
    if vol >= 5000 and 11 <= organic_rank <= 50: return 'S'
    if 1000 <= vol < 5000 and 1 <= organic_rank <= 30: return 'A'
    if 1000 <= vol < 5000 and iq >= 500 and organic_rank > 0: return 'A'
    if vol < 1000 and iq > 0: return 'B'
    if 1000 <= vol < 5000 and organic_rank == 0 and iq > 0: return 'B'
    if vol >= 10000 and iq > 0: return 'S'
    if vol >= 1000 and iq == 0: return 'D'
    return 'D'

def cpr_bucket(cpr):
    if cpr < 8: return '低'
    if cpr < 12: return '中'
    if cpr <= 26: return '高'
    return '极高'

def competition_level(ad_asins, comp_asins):
    if ad_asins < 100 and comp_asins < 50: return '低竞争', 1.0
    if ad_asins < 300: return '中竞争', 0.6
    if ad_asins < 500: return '高竞争', 0.3
    return '红海', 0.1

def calc_priority(iq, cpr, ad_asins, comp_asins, vol):
    iq_norm = min(iq / 2000.0, 1.0) if iq > 0 else 0
    cpr_norm = min(cpr / 50.0, 1.0) if cpr > 0 else 0
    _, comp_weight = competition_level(ad_asins, comp_asins)
    priority = iq_norm * 0.4 + cpr_norm * 0.3 + comp_weight * 0.3
    if vol >= 5000: priority *= 1.1
    return round(priority * 100, 2)

def traffic_level(vol):
    if vol >= 50000: return 'S'
    if vol >= 10000: return 'A'
    if vol >= 5000: return 'B'
    if vol >= 1000: return 'C'
    return 'D'

def blue_ocean(comp):
    if comp is None: return '无数据'
    if comp >= 10000: return '极激烈'
    if comp >= 5000: return '激烈'
    if comp >= 1000: return '一般'
    if comp >= 500: return '温和'
    return '蓝海'

def entry_barrier(aba_conv):
    if aba_conv is None or aba_conv == 0: return '无数据'
    if aba_conv > 70: return '极激烈'
    if aba_conv > 50: return '很高'
    if aba_conv > 30: return '高'
    if aba_conv > 15: return '一般'
    return '友好'

def relevance_level(comp_perf):
    if comp_perf is None: return '无数据'
    if comp_perf >= 8: return '高'
    if comp_perf >= 6: return '中'
    if comp_perf >= 4: return '弱'
    return '不相关'

def recommend_action(vol, traffic_lv, relevance_lv, entry_lv, blue_lv, is_brand):
    """
    四维度递进推荐逻辑：需求(流量) → 竞争(蓝海) → 垄断(ABA) → 相关性

    - 主推: 高相关 + 蓝海/温和（需求旺盛+竞品少+我们能打）
    - 测试: 中相关 + 蓝海/温和（有一定相关性，值得测试）
    - 选品方向: 高需求+低竞品+低垄断+低相关（开发新品满足这部分需求）
    - 品牌壁垒: 高ABA垄断（品牌主导，需人工判断，不一棍子打死）
    - 待确认: 品牌词或需根据实际产品判断（不绝对否定）
    - 观察: 默认
    """
    # 品牌词 → 待确认（不绝对否定，取决于实际产品）
    if is_brand:
        return '待确认'

    # 高ABA垄断 → 品牌壁垒（品牌主导，需人工判断）
    if entry_lv in ('很高', '极激烈'):
        return '品牌壁垒'

    # 高相关(8-10) + 蓝海/温和 = 主推（核心词池）
    if relevance_lv == '高' and blue_lv in ('蓝海', '温和'):
        return '主推'

    # 中相关(6-8) + 蓝海/温和 = 测试
    if relevance_lv == '中' and blue_lv in ('蓝海', '温和'):
        return '测试'

    # 低相关 + 高需求(≥5000) + 低竞品(蓝海/温和) + 低垄断 = 选品方向（开发新品）
    if relevance_lv in ('弱', '不相关', '无数据') and vol >= 5000 and blue_lv in ('蓝海', '温和') and entry_lv in ('友好', '一般', '无数据'):
        return '选品方向'

    # 高相关 + 一般竞争 = 防守
    if relevance_lv == '高' and blue_lv == '一般':
        return '防守'

    # 中相关 + 一般竞争 + 友好/一般准入 = 测试
    if relevance_lv == '中' and blue_lv == '一般' and entry_lv in ('友好', '一般'):
        return '测试'

    # 其他 = 观察
    return '观察'


# ═══════════════════════════════════════════════════════════════
# Attribute-level opportunity aggregation
# ═══════════════════════════════════════════════════════════════

def _calc_attr_opportunities(v41_results, dim_tag_stats):
    """
    对每个属性 tag 聚合需求/竞争/垄断/相关性，
    识别"高需求+低竞品+低垄断"的选品开发方向。
    """
    tag_keywords = defaultdict(list)

    for r in v41_results:
        for dim, val in r['dim_values'].items():
            if val and val != '-':
                for tag in val.split('|'):
                    tag_keywords[tag].append(r)

    opportunities = []
    for tag, kws in tag_keywords.items():
        if len(kws) < 3:
            continue
        total_vol = sum(k['vol'] for k in kws)
        avg_comp = sum(k['comp_asins'] for k in kws) / len(kws)
        # ABA: count high monopoly
        high_mono = sum(1 for k in kws if k['entry_barrier'] in ('高', '很高', '极激烈'))
        mono_rate = high_mono / len(kws)
        # Relevance: count high relevance
        high_rel = sum(1 for k in kws if k['relevance'] == '高')
        rel_rate = high_rel / len(kws)

        # Opportunity score: high demand + low competition + low monopoly
        opp_score = 0
        if total_vol >= 5000:
            opp_score += 30
        elif total_vol >= 1000:
            opp_score += 20
        if avg_comp < 500:
            opp_score += 30
        elif avg_comp < 1000:
            opp_score += 15
        if mono_rate < 0.2:
            opp_score += 25
        elif mono_rate < 0.5:
            opp_score += 10
        if rel_rate < 0.3:
            opp_score += 15  # 低相关 = 选品方向（开发新品）

        opportunities.append({
            'tag': tag,
            'keyword_count': len(kws),
            'total_vol': total_vol,
            'avg_comp': round(avg_comp, 0),
            'monopoly_rate': round(mono_rate, 2),
            'relevance_rate': round(rel_rate, 2),
            'opportunity_score': opp_score,
            'top_keywords': [{'keyword': k['keyword'], 'vol': k['vol']} for k in
                             sorted(kws, key=lambda x: x['vol'], reverse=True)[:3]],
        })

    opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
    return opportunities[:20]


# ═══════════════════════════════════════════════════════════════
# Main pipeline
# ═══════════════════════════════════════════════════════════════

def run_pipeline(xlsx_path, asin, output_dir):
    # S1: Read xlsx
    print(f"[S1] Loading: {xlsx_path}")
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0: continue
        rows.append(list(row))
    wb.close()
    print(f"[S1] {len(rows)} rows loaded")

    # Extract keywords for attribute discovery
    all_keywords = [row[0] for row in rows if row[0] and row[0] != '-']

    # S3 Phase 1: Dynamic attribute discovery
    print("[S3] Discovering attributes from keyword data...")
    dynamic_tree, core_words, token_freq = discover_attributes(all_keywords)

    # Print discovery summary
    dim_counts = {dim: len(tags) for dim, tags in dynamic_tree.items()}
    print(f"[S3] Discovered attribute tree: {sum(dim_counts.values())} tags across {len(dim_counts)} dims")
    print(f"[S3] Core words: {', '.join(list(core_words)[:10])}")
    for dim, count in sorted(dim_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dim}: {count} tags")

    # S2: V3 analysis
    print("[S2] V3 5-step analysis...")
    v3_results = []
    root_counter = Counter()
    for row in rows:
        kw = row[0]
        if not kw or kw == '-': continue
        vol = safe_int(row[5]) or safe_int(row[3])
        iq = safe_int(row[4])
        cpr = safe_float(row[12]) or 0.0
        ad_asins = safe_int(row[10])
        comp_asins = safe_int(row[11])
        organic_rank = safe_int(row[14]) or safe_int(row[27])
        sp_rank = safe_int(row[15])
        core, upper, attr, weak = decompose_keyword(kw, core_words)
        for w in core.split(): root_counter[w] += 1
        tier = traffic_tier(vol)
        grade = v3_classify(vol, iq, organic_rank, weak, kw)
        cpr_b = cpr_bucket(cpr)
        comp_lv, _ = competition_level(ad_asins, comp_asins)
        priority = calc_priority(iq, cpr, ad_asins, comp_asins, vol)
        notes = []
        if 0 < organic_rank <= 10: notes.append(f'首页({organic_rank})')
        elif organic_rank > 10: notes.append(f'排名{organic_rank}')
        if sp_rank > 0: notes.append(f'广告位{sp_rank}')
        if cpr_b in ('高', '极高'): notes.append(f'CPR{cpr_b}')
        if comp_lv == '红海': notes.append('红海')
        if vol >= 10000: notes.append('万级大词')
        v3_results.append({
            'keyword': kw, 'core': core, 'upper': upper, 'attr': attr, 'weak': weak,
            'vol': vol, 'cpr': cpr, 'comp_level': comp_lv, 'ad_asins': ad_asins,
            'comp_asins': comp_asins, 'iq': iq, 'organic_rank': organic_rank,
            'sp_rank': sp_rank,
            'action': {'S': '精确', 'A': '词组', 'B': '广泛', 'C': '否定', 'D': '观察'}.get(grade, '观察'),
            'tier': tier, 'grade': grade, 'priority': priority, 'note': '; '.join(notes),
        })
    v3_results.sort(key=lambda x: x['priority'], reverse=True)
    print(f"[S2] Done: {len(v3_results)} keywords")

    # S3 Phase 2: Tag + evaluate
    print("[S3] Tagging keywords with dynamic attribute tree...")
    DIM_NAMES = list(dynamic_tree.keys())
    v41_results = []
    dim_hit_counter = Counter()
    tag_hit_counter = Counter()
    multi_dim_count = 0

    for row in rows:
        kw = row[0]
        if not kw or kw == '-': continue
        vol = safe_int(row[5]) or safe_int(row[3])
        iq = safe_int(row[4])
        comp_asins = safe_int(row[11])
        organic_rank = safe_int(row[14]) or safe_int(row[27])
        aba_conv = safe_float(row[2])
        comp_perf = safe_float(row[31])

        tags = tag_keyword(kw, dynamic_tree)
        hit_count = len(tags)
        if hit_count >= 4: multi_dim_count += 1
        for dim, tag_list in tags.items():
            dim_hit_counter[dim] += 1
            for t in tag_list: tag_hit_counter[t] += 1

        kw_tokens = set(tokenize((kw or '').lower()))
        is_brand = bool(kw_tokens & BRAND_LIBRARY)
        weak = ' '.join(kw_tokens & BRAND_LIBRARY)
        v3_grade = v3_classify(vol, iq, organic_rank, weak, kw)

        t_lv = traffic_level(vol)
        b_lv = blue_ocean(comp_asins if comp_asins > 0 else None)
        e_lv = entry_barrier(aba_conv)
        r_lv = relevance_level(comp_perf)
        action = recommend_action(vol, t_lv, r_lv, e_lv, b_lv, is_brand)

        dim_values = {}
        for dim in DIM_NAMES:
            dim_values[dim] = '|'.join(tags[dim]) if dim in tags else '-'

        v41_results.append({
            'keyword': kw, 'v3_grade': v3_grade, 'dim_values': dim_values,
            'vol': vol, 'traffic_lv': t_lv, 'comp_asins': comp_asins,
            'blue_ocean': b_lv, 'aba_conv': aba_conv if aba_conv is not None else '',
            'entry_barrier': e_lv, 'comp_perf': comp_perf if comp_perf is not None else '',
            'relevance': r_lv, 'action': action, 'is_brand': is_brand,
            'hit_count': hit_count,
        })
    print(f"[S3] Done: {len(v41_results)} keywords, {multi_dim_count} multi-dim")

    # S4: Output — only V4.1 CSV + enhanced stats JSON
    print("[S4] Writing outputs...")
    v41_csv = os.path.join(output_dir, f'keyword-cosmo-attribute-{asin}-v41.csv')
    stats_json = os.path.join(output_dir, f'analysis-stats-{asin}.json')

    # V4.1 CSV — 数值维度在前，属性维度在后，全部中文化
    DIM_ZH = {
        'INGREDIENT_FAMILY': '成分家族', 'PAIN_SPECIFIC': '痛点细分',
        'FORM_FAMILY': '产品形态', 'AREA_FAMILY': '使用部位',
        'AUDIENCE_FAMILY': '目标人群', 'MODIFIER_FAMILY': '修饰/价值主张',
        'BENEFIT_FAMILY': '功效', 'PURCHASE_CONTEXT': '购买场景',
        'TEMPORAL': '季节事件', 'ORIGIN': '产地文化', 'GENERIC': '通用异常',
    }
    # Load tag translations
    tag_trans_path = os.path.join(SKILL_ROOT, 'assets', 'tag-translations.json')
    tag_trans = {}
    if os.path.isfile(tag_trans_path):
        with open(tag_trans_path, 'r', encoding='utf-8') as f:
            tag_trans = json.load(f)

    def translate_tag(val):
        """Translate tag value to Chinese, handle discovered_ prefix"""
        if not val or val == '-':
            return '-'
        parts = val.split('|')
        translated = []
        for t in parts:
            if t in tag_trans:
                translated.append(tag_trans[t])
            elif t.startswith('discovered_'):
                # Clean up discovered tags: discovered_bulk → bulk, discovered_printable → printable
                clean = t.replace('discovered_', '').replace('_', ' ')
                translated.append(clean)
            elif t.startswith('form_'):
                translated.append(t.replace('form_', '').replace('_', ' '))
            elif t.startswith('benefit_'):
                translated.append(t.replace('benefit_', '').replace('_', ' '))
            elif t.startswith('ingredient_'):
                translated.append(t.replace('ingredient_', '').replace('_', ' '))
            elif t.startswith('audience_'):
                translated.append(t.replace('audience_', '').replace('_', ' '))
            elif t.startswith('area_'):
                translated.append(t.replace('area_', '').replace('_', ' '))
            elif t.startswith('pain_'):
                translated.append(t.replace('pain_', '').replace('_', ' '))
            else:
                translated.append(t.replace('_', ' '))
        return '|'.join(translated)

    dim_names_zh = [DIM_ZH.get(d, d) for d in DIM_NAMES]
    V41_HEADER = ['序号', '关键词', '搜索量', '流量等级', '竞品数', '蓝海度',
                   'ABA转化份额', '准入难度', '竞品表现得分', '相关性等级', '推荐行动'] + dim_names_zh
    with open(v41_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(V41_HEADER)
        for i, r in enumerate(v41_results, 1):
            row_data = [i, r['keyword'], r['vol'], r['traffic_lv'], r['comp_asins'], r['blue_ocean'],
                         r['aba_conv'], r['entry_barrier'], r['comp_perf'], r['relevance'], r['action']]
            for dim in DIM_NAMES:
                row_data.append(translate_tag(r['dim_values'][dim]))
            w.writerow(row_data)

    # ── Four-dimension summary report ──
    grade_counts = Counter(x['grade'] for x in v3_results)
    action_counts = Counter(r['action'] for r in v41_results)
    traffic_counts = Counter(r['traffic_lv'] for r in v41_results)
    blue_counts = Counter(r['blue_ocean'] for r in v41_results)
    entry_counts = Counter(r['entry_barrier'] for r in v41_results)
    relevance_counts = Counter(r['relevance'] for r in v41_results)

    # Dim tag stats
    dim_tag_stats = {}
    for dim in DIM_NAMES:
        dim_tags = {}
        for tag_name in dynamic_tree[dim]:
            if tag_name in tag_hit_counter:
                dim_tags[tag_name] = tag_hit_counter[tag_name]
        dim_tag_stats[dim] = sorted(dim_tags.items(), key=lambda x: x[1], reverse=True)[:5]

    # Serialize dynamic tree
    dynamic_tree_serializable = {}
    for dim, tags in dynamic_tree.items():
        dynamic_tree_serializable[dim] = {tag: list(pats) for tag, pats in tags.items()}

    # ── Dim 1: Traffic level — top keywords per grade ──
    traffic_top = {}
    for lv in ['S', 'A', 'B', 'C', 'D']:
        lv_words = sorted([r for r in v41_results if r['traffic_lv'] == lv],
                          key=lambda x: x['vol'], reverse=True)[:10]
        traffic_top[lv] = [{'keyword': r['keyword'], 'vol': r['vol'], 'comp_asins': r['comp_asins'],
                            'blue_ocean': r['blue_ocean'], 'action': r['action']} for r in lv_words]

    # ── Dim 2: Blue ocean — blue ocean keywords + red ocean keywords ──
    blue_ocean_words = sorted([r for r in v41_results if r['blue_ocean'] == '蓝海'],
                              key=lambda x: x['vol'], reverse=True)[:20]
    red_ocean_words = sorted([r for r in v41_results if r['blue_ocean'] in ('激烈', '极激烈')],
                             key=lambda x: x['vol'], reverse=True)[:10]

    # ── Dim 3: ABA monopoly — high vs low monopoly ──
    high_monopoly = sorted([r for r in v41_results if r['entry_barrier'] in ('极高', '很高', '高')],
                           key=lambda x: (x['aba_conv'] if isinstance(x['aba_conv'], (int, float)) else 0), reverse=True)[:15]
    low_monopoly = sorted([r for r in v41_results if r['entry_barrier'] in ('友好', '一般')],
                          key=lambda x: x['vol'], reverse=True)[:15]

    # ── Dim 4: Relevance — high relevance precise keywords ──
    high_relevance = sorted([r for r in v41_results if r['relevance'] == '高'],
                            key=lambda x: x['vol'], reverse=True)[:20]

    # ── Action recommendation summary ──
    action_top = {}
    for act in ['主推', '测试', '选品方向', '品牌壁垒', '待确认', '防守', '观察']:
        act_words = sorted([r for r in v41_results if r['action'] == act],
                           key=lambda x: x['vol'], reverse=True)[:10]
        action_top[act] = [{'keyword': r['keyword'], 'vol': r['vol'], 'blue_ocean': r['blue_ocean'],
                            'entry_barrier': r['entry_barrier'], 'relevance': r['relevance']} for r in act_words]

    multi_results = sorted([r for r in v41_results if r['hit_count'] >= 4],
                           key=lambda x: x['vol'], reverse=True)[:10]

    stats = {
        # 大盘概览
        'total_keywords': len(v41_results),
        'brand_count': sum(1 for r in v41_results if r['is_brand']),
        'discovered_core_words': sorted(core_words),
        'top_tokens': token_freq.most_common(20),
        'dim_hit_counts': dict(dim_hit_counter),
        'dim_tag_stats': {dim: [[t, c] for t, c in tags] for dim, tags in dim_tag_stats.items()},

        # 维度一：流量等级
        'traffic_summary': {
            'distribution': dict(traffic_counts),
            'top_keywords': traffic_top,
        },

        # 维度二：蓝海程度
        'blue_ocean_summary': {
            'distribution': dict(blue_counts),
            'blue_ocean_top': [{'keyword': r['keyword'], 'vol': r['vol'],
                                'comp_asins': r['comp_asins'], 'action': r['action']} for r in blue_ocean_words],
            'red_ocean_top': [{'keyword': r['keyword'], 'vol': r['vol'],
                               'comp_asins': r['comp_asins']} for r in red_ocean_words],
        },

        # 维度三：ABA垄断度
        'aba_monopoly_summary': {
            'distribution': dict(entry_counts),
            'high_monopoly_top': [{'keyword': r['keyword'], 'vol': r['vol'],
                                   'aba_conv': r['aba_conv'], 'entry_barrier': r['entry_barrier']} for r in high_monopoly],
            'low_monopoly_top': [{'keyword': r['keyword'], 'vol': r['vol'],
                                  'aba_conv': r['aba_conv'], 'entry_barrier': r['entry_barrier']} for r in low_monopoly],
        },

        # 维度四：相关性
        'relevance_summary': {
            'distribution': dict(relevance_counts),
            'high_relevance_top': [{'keyword': r['keyword'], 'vol': r['vol'],
                                    'relevance': r['relevance'], 'action': r['action']} for r in high_relevance],
        },

        # 行动建议
        'action_summary': {
            'distribution': dict(action_counts),
            'top_keywords': action_top,
        },

        # V3 grade + dynamic tree (for reference)
        'v3_grade_counts': dict(grade_counts),
        'dynamic_attribute_tree': dynamic_tree_serializable,
        'top_roots': root_counter.most_common(20),
        'multi_dim_count': multi_dim_count,
        'top_multi_dim': [{
            'keyword': r['keyword'], 'vol': r['vol'], 'hit_count': r['hit_count'],
            'tags': {k: v for k, v in r['dim_values'].items() if v != '-'},
        } for r in multi_results],

        # 属性维度选品方向：每个属性 tag 下的需求/竞争/垄断/相关性聚合
        'attribute_opportunities': _calc_attr_opportunities(v41_results, dim_tag_stats),
    }
    with open(stats_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Verify CSV
    with open(v41_csv, 'r', encoding='utf-8-sig') as f:
        rows_check = list(csv.reader(f))
    h_cols = len(rows_check[0])
    broken = [(i, len(r)) for i, r in enumerate(rows_check) if len(r) != h_cols]
    status = f"BROKEN {len(broken)} rows" if broken else f"OK ({len(rows_check)-1} rows x {h_cols} cols)"
    print(f"  {os.path.basename(v41_csv)}: {status}")

    print(f"\n===== DONE =====")
    print(f"V4.1 CSV:   {v41_csv}")
    print(f"Stats JSON: {stats_json}")
    return stats


def main():
    parser = argparse.ArgumentParser(description='Cerebro Keyword Full Analysis (V3 + V4.1 Dynamic)')
    parser.add_argument('--xlsx-path', required=True)
    parser.add_argument('--asin', default='UNKNOWN')
    parser.add_argument('--output-dir', default='.')
    args = parser.parse_args()
    run_pipeline(args.xlsx_path, args.asin, args.output_dir)


if __name__ == '__main__':
    main()
