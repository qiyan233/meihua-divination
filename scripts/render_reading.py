#!/usr/bin/env python3
import argparse
import json
import os
import hashlib

from generate_reading_seed import build_seed
from cast_symbols import cast

GEN = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
CTRL = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

ELEMENT_META = {
    '木': {
        'name': '生发之气',
        'core': '主开路、起意、生长、扩展',
        'risk': '也容易心急、飘、根基未稳'
    },
    '火': {
        'name': '明动之气',
        'core': '主点亮、加速、外显、推动',
        'risk': '也容易过热、躁进、烧得太快'
    },
    '土': {
        'name': '承载之气',
        'core': '主承接、现实、稳定、盘面',
        'risk': '也容易迟滞、负重、推进偏慢'
    },
    '金': {
        'name': '裁断之气',
        'core': '主规则、边界、判断、取舍',
        'risk': '也容易偏硬、偏冷、压感较重'
    },
    '水': {
        'name': '蓄藏之气',
        'core': '主隐伏、观察、回收、等待时机',
        'risk': '也容易多想、迟疑、回流不前'
    }
}

MODE_TO_CHINESE = {
    'general': '综合断事',
    'career': '事业 / 项目 / 决策',
    'relationship': '关系解读',
    'fortune': '当前运势 / 阶段气运',
    'personality': '人设 / 性格 / 天赋倾向'
}


def load_library():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, '..', 'assets', 'phrase-library.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def token(seed, slot):
    h = hashlib.sha256((seed + '|' + slot).encode('utf-8')).hexdigest()
    return int(h[:12], 16)


def choose(seed, slot, items):
    if not items:
        return ''
    return items[token(seed, slot) % len(items)]


def effect_on_subject(subject, other):
    if subject == other:
        return '比和'
    if GEN[other] == subject:
        return '生我'
    if CTRL[other] == subject:
        return '克我'
    if GEN[subject] == other:
        return '泄我'
    if CTRL[subject] == other:
        return '我克'
    return '未知'


def role_line(role, item):
    meta = ELEMENT_META[item['element']]
    motion = '动' if item['dynamic'] == '动' else '静'
    strength = '偏强' if item['strength'] == '强' else '偏弱'
    flow = '顺势' if item['flow'] == '顺' else '逆势'
    return '%s见%s，为%s；其性%s，且%s。' % (
        role, item['element'], meta['name'], motion + '、' + strength, flow
    )


def score_reading(roles):
    main = roles['主象']
    guest = roles['客象']
    block = roles['阻象']
    change = roles['变象']
    response = roles['应象']

    env = effect_on_subject(main['element'], guest['element'])
    obstacle = effect_on_subject(main['element'], block['element'])
    trend = effect_on_subject(main['element'], change['element'])
    response_to_main = effect_on_subject(main['element'], response['element'])
    response_to_block = effect_on_subject(block['element'], response['element'])

    score = 0
    risk = 0

    if main['element'] in ('木', '火'):
        score += 1
    if main['element'] in ('土', '水'):
        score -= 1
    if main['dynamic'] == '动':
        score += 1
    else:
        score -= 1

    if env == '生我':
        score += 2
    elif env == '比和':
        score += 1
    elif env == '我克':
        score += 0
        risk += 1
    elif env == '泄我':
        score -= 1
        risk += 1
    elif env == '克我':
        score -= 2
        risk += 2

    if obstacle == '克我':
        risk += 2
        score -= 1
    elif obstacle == '泄我':
        risk += 2
        score -= 1
    elif obstacle == '比和':
        risk += 1
    elif obstacle == '我克':
        risk += 1

    if change == '生我':
        score += 1
    elif change == '克我':
        risk += 1
        score -= 1
    elif change == '泄我':
        score -= 1
        risk += 1

    if response_to_main == '生我':
        score += 1
    elif response_to_main == '泄我':
        risk += 1

    if response_to_block == '我克':
        score += 1
        risk = max(0, risk - 1)
    elif response_to_block == '生我':
        risk += 1

    if guest['dynamic'] == '动':
        score += 1
    if block['strength'] == '强':
        risk += 1
    if change['flow'] == '逆':
        risk += 1

    return {
        'env_effect': env,
        'obstacle_effect': obstacle,
        'trend_effect': trend,
        'response_on_main': response_to_main,
        'response_on_obstacle': response_to_block,
        'score': score,
        'risk': risk
    }


def decide_key(mode, roles, metrics):
    guest = roles['客象']
    block = roles['阻象']
    change = roles['变象']
    main = roles['主象']

    if metrics['env_effect'] in ('生我', '比和') and metrics['obstacle_effect'] in ('克我', '泄我', '比和'):
        if guest['flow'] == '顺' and block['strength'] == '强':
            return 'outer_block'

    if change['element'] in ('金', '火') and metrics['response_on_obstacle'] == '克我' and metrics['risk'] >= 2:
        return 'break_build'

    if metrics['score'] >= 3 and metrics['risk'] <= 2 and main['dynamic'] == '动':
        return 'move'

    if metrics['score'] <= 0 or (main['dynamic'] == '静' and metrics['risk'] >= 2):
        return 'hold'

    return 'cautious'


def build_reason(seed, library, roles, metrics):
    main = roles['主象']
    guest = roles['客象']
    block = roles['阻象']
    change = roles['变象']

    relation_phrases = library['relation_phrases']
    p_env = choose(seed, 'reason-env', relation_phrases.get(metrics['env_effect'], ['']))
    p_block = choose(seed, 'reason-block', relation_phrases.get(metrics['obstacle_effect'], ['']))

    trend_map = {
        '生我': '得扶而续，后势较易转稳',
        '克我': '受压而改，后势多带修正之意',
        '泄我': '外泄而散，后势易有耗力与分神',
        '我克': '需主动用力，后势成于取舍与控制',
        '比和': '同气相叠，后势会放大当前倾向'
    }
    trend_line = trend_map.get(metrics['trend_effect'], '后势仍有变化，不会原样停留')

    guest_line_map = {
        '生我': '外部条件对你有托举之意',
        '克我': '外部压力对你有压制之势',
        '泄我': '这件事会持续牵扯你的心力与投入',
        '我克': '你对外部局面并非无力，但需要自己多出手整合',
        '比和': '外部情势与你当前心气较为同频，会相互放大'
    }
    guest_line = guest_line_map.get(metrics['env_effect'], '外部情势与内在状态互有牵连')

    block_line_map = {
        '生我': '这道阻力未必全坏，其中也带一点逼你成形的压力',
        '克我': '这里是直接卡住你的地方，不宜硬顶',
        '泄我': '这里最容易耗神耗力，久拖则气会散',
        '我克': '你并非不能处理，只是处理它要花成本',
        '比和': '这更像内外同类之阻，容易在同一个毛病上反复打转'
    }
    block_line = block_line_map.get(metrics['obstacle_effect'], '这里确实是当下绕不开的一处卡点')

    lines = []
    lines.append('主象见%s，属%s，%s。' % (main['element'], ELEMENT_META[main['element']]['name'], ELEMENT_META[main['element']]['core']))
    lines.append('客象见%s，%s；从体用关系看，可概括为“%s”。' % (guest['element'], guest_line, p_env))
    lines.append('阻象见%s，说明真正的卡点不只在外面，更在结构、节奏或心力分配上；%s。' % (block['element'], block_line))
    lines.append('变象见%s，表示后势不会原样停着不动，整体更像“%s”。' % (change['element'], trend_line))
    return ' '.join(lines)


def manifestation_speed(roles):
    moving = 0
    if roles['主象']['dynamic'] == '动':
        moving += 1
    if roles['客象']['dynamic'] == '动':
        moving += 2
    if roles['阻象']['dynamic'] == '动':
        moving += 1
    if roles['变象']['dynamic'] == '动':
        moving += 2
    if roles['应象']['dynamic'] == '动':
        moving += 1

    if moving >= 5:
        return '快'
    if moving <= 1:
        return '慢'
    return '中'


def build_phased_trend(seed, roles, metrics, mode):
    guest = roles['客象']
    block = roles['阻象']
    change = roles['变象']
    speed = manifestation_speed(roles)

    near_templates = {
        '生我': '近势外缘对你有扶托，眼前不算全闭',
        '克我': '近势外压先到，眼前会先感到受制',
        '泄我': '近势最明显的是耗神耗力，事情会牵着你走',
        '我克': '近势要靠你主动出手整合，不能只等局面自己变好',
        '比和': '近势同气相引，眼前会放大你当前的心气与动作'
    }
    mid_templates = {
        '生我': '中势的卡点未必全坏，反而可能逼你把结构补出来',
        '克我': '中势真正要过的是硬障，不调整结构就容易反复撞墙',
        '泄我': '中势最怕久拖，拖久了气会散，问题会从小耗变成大耗',
        '我克': '中势不是不能过，而是每推进一步都要付出成本',
        '比和': '中势容易在同一类问题上反复打转，若不改方法就会原地消耗'
    }
    late_templates = {
        '生我': '后势有转稳之意，越往后越容易看见成形',
        '克我': '后势带修正压力，不改法则后面仍会觉得紧',
        '泄我': '后势怕继续外泄，若不收口，越到后面越疲',
        '我克': '后势成于取舍与控制，敢收、敢断、敢整合，路会出来',
        '比和': '后势会把现在的倾向继续放大，方向对就越走越顺，方向错也会越走越偏'
    }

    near = near_templates.get(metrics['env_effect'], '近势已有显象，但还要继续看外势怎么落')
    middle = mid_templates.get(metrics['obstacle_effect'], '中势的关键在过程承接，而不只在一时判断')
    later = late_templates.get(metrics['trend_effect'], '后势仍会转化，暂不算定局')

    speed_line = {
        '快': '整体动象不弱，显化偏快，近期较容易见到回音。',
        '中': '动静参半，事情会逐步显化，不是一蹴而就。',
        '慢': '整体偏静，端倪未全显，更像在蓄势待成。'
    }[speed]

    if mode == 'relationship' and speed == '快':
        speed_line = '情势已有波动，回应快慢会比你想的更明显，但也更怕用力过头。'
    elif mode == 'career' and speed == '快':
        speed_line = '局面已有动象，近期容易看到反馈，但反馈未必等于已经稳成。'
    elif mode == 'fortune' and speed == '慢':
        speed_line = '这一段更像回气期，不是立刻翻盘期，先调顺比先提速更重要。'

    return '近势：%s；中势：%s；后势：%s。%s' % (near, middle, later, speed_line)


def build_advice(seed, library, roles, metrics, mode, verdict_key):
    response = roles['应象']
    main = roles['主象']
    element_advice = choose(seed, 'advice-el', library['advice_by_element'][response['element']])
    mode_advice_bank = library.get('mode_advice', {}).get(mode, library.get('mode_advice', {}).get('general', {}))
    mode_advice = choose(seed, 'mode-advice', mode_advice_bank.get(verdict_key, ['']))
    extra = []

    if mode_advice:
        extra.append(mode_advice)

    risk_bank = library.get('risk_lines', {}).get(mode, library.get('risk_lines', {}).get('general', []))
    if metrics['risk'] >= 3 and risk_bank:
        extra.append(choose(seed, 'risk-line', risk_bank))

    if response['element'] == main['element']:
        extra.append('应象与主象同气，说明最有效的解法往往不是换人格，而是把你本来的长处用对地方。')

    return element_advice + ' ' + ' '.join(extra)


def build_signature(seed, library, verdict_key, mode):
    sig_bank = library['signatures'].get(mode, library['signatures']['general'])
    return choose(seed, 'signature', sig_bank[verdict_key])


def render(mode, question, context='', date='', style='standard', seed=None):
    library = load_library()
    final_seed = seed or build_seed([mode, question, context, date])
    roles = cast(final_seed, mode)
    metrics = score_reading(roles)
    metrics['manifestation_speed'] = manifestation_speed(roles)
    verdict_key = decide_key(mode, roles, metrics)

    judgments = library['judgments'].get(mode, library['judgments']['general'])
    verdict = choose(final_seed, 'judgment', judgments[verdict_key])
    reason = build_reason(final_seed, library, roles, metrics)
    trend = build_phased_trend(final_seed, roles, metrics, mode)
    advice = build_advice(final_seed, library, roles, metrics, mode, verdict_key)
    signature = build_signature(final_seed, library, verdict_key, mode)

    role_lines = [role_line(role, roles[role]) for role in ['主象', '客象', '阻象', '变象', '应象']]
    dynamic_summary = '；'.join(role_lines)

    data = {
        'mode': mode,
        'mode_label': library['mode_labels'].get(mode, MODE_TO_CHINESE.get(mode, mode)),
        'question': question,
        'seed': final_seed,
        'roles': roles,
        'analysis': metrics,
        'verdict_key': verdict_key,
        'reading': {
            '总断': verdict,
            '生克与动静': dynamic_summary,
            '断因': reason,
            '断势': trend,
            '断法': advice,
            '签语': signature
        }
    }

    if style == 'quick':
        text = '\n'.join([
            '总断：' + data['reading']['总断'],
            '断因：' + data['reading']['断因'],
            '断法：' + data['reading']['断法'],
            '签语：' + data['reading']['签语']
        ])
    elif style == 'deep':
        text = '\n'.join([
            '问题归类：' + data['mode_label'],
            '问题：' + question,
            '主象：' + json.dumps(roles['主象'], ensure_ascii=False),
            '客象：' + json.dumps(roles['客象'], ensure_ascii=False),
            '阻象：' + json.dumps(roles['阻象'], ensure_ascii=False),
            '变象：' + json.dumps(roles['变象'], ensure_ascii=False),
            '应象：' + json.dumps(roles['应象'], ensure_ascii=False),
            '生克与动静：' + data['reading']['生克与动静'],
            '总断：' + data['reading']['总断'],
            '断因：' + data['reading']['断因'],
            '断势：' + data['reading']['断势'],
            '断法：' + data['reading']['断法'],
            '签语：' + data['reading']['签语']
        ])
    else:
        text = '\n'.join([
            '总断：' + data['reading']['总断'],
            '断因：' + data['reading']['断因'],
            '断势：' + data['reading']['断势'],
            '断法：' + data['reading']['断法'],
            '签语：' + data['reading']['签语']
        ])

    data['text'] = text
    return data


def main():
    parser = argparse.ArgumentParser(description='Render a structured Chinese-style divination reading.')
    parser.add_argument('--mode', default='general', choices=['general', 'career', 'relationship', 'fortune', 'personality'])
    parser.add_argument('--question', required=True)
    parser.add_argument('--context', default='')
    parser.add_argument('--date', default='')
    parser.add_argument('--style', default='standard', choices=['quick', 'standard', 'deep'])
    parser.add_argument('--seed', default='')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    out = render(
        mode=args.mode,
        question=args.question,
        context=args.context,
        date=args.date,
        style=args.style,
        seed=args.seed or None
    )

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(out['text'])


if __name__ == '__main__':
    main()
