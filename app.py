from flask import Flask, request, render_template_string, jsonify
from policy_analyzer import PolicyAnalyzer
import os
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

try:
    analyzer = PolicyAnalyzer()
    print("PolicyAnalyzer initialized successfully")
except Exception as e:
    print(f"Failed to initialize PolicyAnalyzer: {e}")
    analyzer = None


def clean_text(text):
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    return text.strip()


def clean_for_pdf(text):
    """PDF용 텍스트 - 이모지/특수문자 제거, 섹션 헤더 정리"""
    # ASCII + 줄바꿈만 남기기
    text = re.sub(r'[^\x00-\x7F\n]', '', text)
    # 마크다운 제거
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # 구분선 통일
    text = re.sub(r'[=%#]{3,}', '---', text)
    text = re.sub(r'-{4,}', '---', text)
    # 섹션 헤더 - 중복 방지
    for section in ['RELEVANT POLICY SECTIONS', 'COMPLIANCE VERDICT', 'RISK ASSESSMENT',
                    'PROFESSOR INTERPRETATIONS', 'RECOMMENDATIONS', 'POLICY CRITIQUE']:
        # [ SECTION ] 이 아닌 경우만 교체
        pattern = r'(?<!\[ )' + re.escape(section) + r'(?! \])'
        text = re.sub(pattern, '\n[ ' + section + ' ]\n', text)
    # 연속 빈줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_between(text, start_kw, stop_kws, max_len=400):
    """start_kw부터 stop_kws 중 가장 먼저 나오는 것까지 추출"""
    upper = text.upper()
    idx = upper.find(start_kw.upper())
    if idx == -1:
        return None

    start = idx + len(start_kw)
    # 콜론, 공백, 줄바꿈 스킵
    while start < len(text) and text[start] in [':', '*', ' ', '\n']:
        start += 1

    # 가장 가까운 stop 키워드 찾기
    end = len(text)
    for kw in stop_kws:
        pos = upper.find(kw.upper(), start + 10)  # 최소 10자 이후부터 탐색
        if pos != -1 and pos < end:
            end = pos

    excerpt = text[start:min(start + max_len, end)]
    return clean_text(excerpt) or None


def parse_analysis(text):
    result = {}
    upper = text.upper()

    # 섹션 경계 미리 계산 (상위 섹션 헤더들의 위치)
    section_markers = [
        'COMPLIANCE VERDICT', 'RISK ASSESSMENT', 'PROFESSOR INTERPRETATIONS',
        'RECOMMENDATIONS', 'POLICY CRITIQUE', 'POLICY EFFECTIVENESS'
    ]

    def next_section(from_pos):
        """from_pos 이후 가장 가까운 섹션 헤더 위치 반환"""
        nearest = len(text)
        for marker in section_markers:
            pos = upper.find(marker, from_pos + 20)
            if pos != -1 and pos < nearest:
                nearest = pos
        # 구분선도 경계로
        for sep in ['\n━', '\n---', '\n===', '\n%%%']:
            pos = text.find(sep, from_pos + 20)
            if pos != -1 and pos < nearest:
                nearest = pos
        return nearest

    def get_section_text(start_kw, max_len=800):
        """start_kw 이후부터 다음 섹션까지 텍스트 추출"""
        idx = upper.find(start_kw)
        if idx == -1:
            return None
        start_pos = idx + len(start_kw)
        while start_pos < len(text) and text[start_pos] in [':', '*', ' ', '\n', '-', '=']:
            start_pos += 1
        end_pos = next_section(idx)
        excerpt = text[start_pos:min(start_pos + max_len, end_pos)]
        return clean_text(excerpt) or None

    # ── Verdict ──────────────────────────────────────────────
    if 'GRAY AREA' in upper:
        result['verdict'] = {
            'type': 'gray',
            'reasoning': get_section_text('REASONING:') or get_section_text('REASONING') or 'Policy is unclear.'
        }
    elif 'VIOLATION' in upper and 'ALLOWED' not in upper:
        result['verdict'] = {
            'type': 'violation',
            'reasoning': get_section_text('REASONING:') or get_section_text('REASONING') or 'Violates policy.'
        }
    elif 'ALLOWED' in upper:
        result['verdict'] = {
            'type': 'allowed',
            'reasoning': get_section_text('REASONING:') or get_section_text('REASONING') or 'Complies with policy.'
        }

    # ── Risk ──────────────────────────────────────────────────
    risk_match = re.search(r'Risk Score:\s*(\d+)/100', text)
    if risk_match:
        score = int(risk_match.group(1))
        level = 'r-low' if score < 30 else 'r-med' if score < 60 else 'r-high' if score < 80 else 'r-crit'
        explanation = get_section_text('EXPLANATION:') or get_section_text('EXPLANATION') or ''
        result['risk'] = {'score': score, 'level': level, 'explanation': explanation}

    # ── Recommendations ───────────────────────────────────────
    # RECOMMENDATIONS 섹션 위치 찾기
    rec_idx = upper.find('RECOMMENDATIONS')
    if rec_idx != -1:
        rec_end = next_section(rec_idx)
        rec_block = text[rec_idx:rec_end]
        rec_upper = rec_block.upper()

        recs = []

        # SAFEST 파트
        s_idx = rec_upper.find('SAFEST')
        m_idx = rec_upper.find('MODERATE')
        a_idx = rec_upper.find('AVOID')

        if s_idx != -1:
            s_start = s_idx + 6
            while s_start < len(rec_block) and rec_block[s_start] in [':', '*', ' ', '\n']:
                s_start += 1
            s_end = m_idx if m_idx > s_idx else (a_idx if a_idx > s_idx else len(rec_block))
            safe_text = clean_text(rec_block[s_start:s_start + 400] if s_end - s_start > 400 else rec_block[s_start:s_end])
            if safe_text:
                recs.append({'type': 'safe', 'label': 'Safest Approach', 'text': safe_text})

        if m_idx != -1:
            m_start = m_idx + 8
            while m_start < len(rec_block) and rec_block[m_start] in [':', '*', ' ', '\n']:
                m_start += 1
            m_end = a_idx if a_idx > m_idx else len(rec_block)
            mod_text = clean_text(rec_block[m_start:m_start + 400] if m_end - m_start > 400 else rec_block[m_start:m_end])
            if mod_text:
                recs.append({'type': 'moderate', 'label': 'Moderate Risk', 'text': mod_text})

        if a_idx != -1:
            a_start = a_idx + 5
            while a_start < len(rec_block) and rec_block[a_start] in [':', '*', ' ', '\n']:
                a_start += 1
            avoid_text = clean_text(rec_block[a_start:a_start + 400])
            if avoid_text:
                recs.append({'type': 'avoid', 'label': 'Avoid', 'text': avoid_text})

        if recs:
            result['recommendations'] = recs

    # ── Policy Critique ───────────────────────────────────────
    score_match = re.search(r'Policy Effectiveness.*?(\d+)/100', text, re.DOTALL)
    if score_match:
        result['policy_score'] = int(score_match.group(1))

    # critique: POLICY CRITIQUE 섹션 전체
    crit_idx = upper.find('POLICY CRITIQUE')
    if crit_idx == -1:
        crit_idx = upper.find('CRITICAL EVALUATION')
    if crit_idx != -1:
        crit_end = next_section(crit_idx)
        critique_raw = text[crit_idx:crit_end]
        # 헤더 제거
        critique_raw = re.sub(r'(?i)policy critique\s*', '', critique_raw, count=1)
        critique_raw = re.sub(r'(?i)critical evaluation\s*', '', critique_raw, count=1)
        # 스코어 숫자 제거
        critique_raw = re.sub(r'Score:\s*\d+/100\s*', '', critique_raw)
        critique_raw = re.sub(r'^\d+/100\s*', '', critique_raw)
        # 마크다운 bold 완전 제거
        critique_raw = re.sub(r'\*\*(.+?)\*\*', r'\1', critique_raw)
        # 단독 ** 제거 (잘린 마크다운)
        critique_raw = re.sub(r'\*+', '', critique_raw)
        # 앞뒤 구분선(━, ---, ===, %%%...) 및 콜론 제거
        critique_raw = re.sub(r'^[\s\-=\u2501\u2500%#:\n]+', '', critique_raw)
        critique_raw = re.sub(r'[\s\-=\u2501\u2500%#\n]+$', '', critique_raw)
        # 줄바꿈 보존하면서 각 줄 앞뒤 공백만 정리
        lines = [line.strip() for line in critique_raw.split('\n')]
        critique_clean = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()
        if critique_clean:
            result['policy_critique'] = critique_clean

    return result


@app.route('/')
def index():
    return render_template_string(open('template.html').read())


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if analyzer is None:
            return jsonify({'error': 'Analyzer not initialized. Check GEMINI_API_KEY'}), 500
        if 'policy' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        policy_file = request.files['policy']
        action = request.form.get('action', '').strip()

        if not action:
            return jsonify({'error': 'Please describe your action'}), 400

        print(f"File: {policy_file.filename} | Action: {action[:60]}...")

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], policy_file.filename)
        policy_file.save(filepath)

        result_text = analyzer.analyze(filepath, action)
        print(f"Done ({len(result_text)} chars)")

        result_data = parse_analysis(result_text)
        result_data['full_text'] = result_text
        result_data['pdf_text'] = clean_for_pdf(result_text)

        return jsonify(result_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        err_str = str(e)
        # Gemini 서버 과부하 에러 친절하게 처리
        if '503' in err_str or 'UNAVAILABLE' in err_str or 'high demand' in err_str:
            msg = 'Gemini API is temporarily overloaded. Please wait 10–30 seconds and try again.'
        elif '429' in err_str or 'quota' in err_str.lower():
            msg = 'API rate limit reached. Please wait a moment and try again.'
        elif 'API_KEY' in err_str or 'api_key' in err_str:
            msg = 'Invalid or missing GEMINI_API_KEY. Please check your environment variable.'
        else:
            msg = err_str
        return jsonify({'error': msg}), 500


if __name__ == '__main__':
    key_status = 'SET' if os.environ.get('GEMINI_API_KEY') else 'NOT SET'
    print(f"Starting | GEMINI_API_KEY: {key_status}")
    app.run(host='0.0.0.0', port=5000, debug=True)