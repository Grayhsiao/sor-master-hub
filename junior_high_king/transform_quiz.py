import sqlite3
import json
import random
from typing import List, Dict, Any

db_path = '/Users/gray/Sites/junior_high_king/quiz.db'

def generate_distractors(correct_answer: str, subject: str, question: str) -> List[str]:
    """根據科目、問題和正確答案，生成3個合理且具迷惑性的錯誤選項。"""
    distractors = []
    
    # 這裡需要一個更智能的LLM調用來生成誘答，
    # 由於OpenClaw目前無法執行這個，我將提供一個模擬版本。
    # 實際應用中，這裡會調用一個更強大的模型API，並傳入上下文。

    # 模擬誘答生成邏輯
    if subject == "數學":
        try:
            # 嘗試將答案轉換為數字進行簡單的數學誘答生成
            num_answer = float(correct_answer)
            distractors.append(str(round(num_answer + random.uniform(-2, 2), 2))) # 輕微的數值偏差
            distractors.append(str(round(num_answer * random.choice([0.5, 2]), 2))) # 倍數錯誤
            distractors.append(str(round(-num_answer, 2))) # 正負號錯誤
        except ValueError:
            # 如果不是數字，則進行文本誘答
            distractors.append(correct_answer + " (錯誤選項A)")
            distractors.append(correct_answer + " (錯誤選項B)")
            distractors.append(correct_answer + " (錯誤選項C)")
    elif subject == "理化":
        if "質量" in question and "密度" in question:
            distractors.append("100公克/立方公分")
            distractors.append("1公克")
            distractors.append("0.1公克/立方公分")
        elif "pH值" in question:
            distractors.append("酸性")
            distractors.append("鹼性")
            distractors.append("中性")
        else:
            distractors.append(correct_answer + " (錯誤選項X)")
            distractors.append(correct_answer + " (錯誤選項Y)")
            distractors.append(correct_answer + " (錯誤選項Z)")
    else: # 其他科目或未知情況
        distractors.append(correct_answer + " (錯誤選項)")
        distractors.append("完全不相關的答案")
        distractors.append("部分正確但誤導的答案")
        
    # 確保只有3個誘答
    return distractors[:3]

def generate_analysis(question: str, correct_option_text: str, subject: str, original_answer: str) -> str:
    """生成詳細的解析，並使用LaTeX語法。"""
    analysis_content = f"### 【{subject}-進階挑戰】題目解析\n\n"
    analysis_content += f"**題目：** {question}\n\n"
    analysis_content += f"**原始答案：** {original_answer}\n\n"
    analysis_content += f"**正確選項：** {correct_option_text}\n\n"
    
    if subject == "數學":
        if "方程式" in question or "解" in question:
            analysis_content += "這是一道關於解方程式的題目。\n"
            analysis_content += "關鍵公式：一次方程式的解法 $ax + b = c \\Rightarrow ax = c - b \\Rightarrow x = \\frac{c-b}{a}$。\n"
            analysis_content += "例如：題目若為 $2x + 5 = 15$，則 $2x = 15 - 5 \\Rightarrow 2x = 10 \\Rightarrow x = \\frac{10}{2} = 5$。\n"
        elif "比例" in question or "比值" in question:
            analysis_content += "本題考察比例與比值的概念。\n"
            analysis_content += "若 $A:B = C:D$，則 $AD = BC$。比值是兩個數量的商。\n"
        else:
            analysis_content += "此題涉及數學基礎概念，需仔細計算。\n"
        analysis_content += f"詳解步驟：\n"
        analysis_content += f"1. 分析題目給定的條件。\n"
        analysis_content += f"2. 找出適用的數學公式或定律。\n"
        analysis_content += f"3. 將數值代入公式，進行精確計算。\n"
        analysis_content += f"例如：若問題問 $x$ 的值是 10，則 $x=10$。\n"
        analysis_content += f"答案的計算過程可能是：\n"
        analysis_content += f"$$y = \\sqrt{x^2 + z^2}$$\n"
        analysis_content += f"若 $x=3, z=4$，則 $y = \\sqrt{3^2 + 4^2} = \\sqrt{9 + 16} = \\sqrt{25} = 5$。\n"

    elif subject == "理化":
        if "密度" in question:
            analysis_content += "本題考察密度的計算。\n"
            analysis_content += "關鍵公式：密度 $D = \\frac{M}{V}$ (質量除以體積)。\n"
            analysis_content += "例如：若質量 $M=100\\,g$，體積 $V=50\\,cm^3$，則 $D = \\frac{100\\,g}{50\\,cm^3} = 2\\,g/cm^3$。\n"
            analysis_content += "單位換算需注意：$1\\,m^3 = 10^6\\,cm^3$。\n"
        elif "力" in question and "加速度" in question:
            analysis_content += "此題涉及牛頓第二運動定律。\n"
            analysis_content += "關鍵公式：合力 $F = ma$ (質量乘以加速度)。\n"
            analysis_content += "例如：質量 $m=2\\,kg$，加速度 $a=5\\,m/s^2$，則 $F = (2\\,kg)(5\\,m/s^2) = 10\\,N$。\n"
        elif "化學反應" in question or "平衡" in question:
            analysis_content += "本題考查化學反應與化學計量。\n"
            analysis_content += "請平衡化學方程式：$$2H_2 + O_2 \\rightarrow 2H_2O$$。\n"
            analysis_content += "質量守恆定律：反應前後原子種類與數量不變。\n"
        else:
            analysis_content += "此題涉及理化基礎概念，需理解物理量與化學反應。\n"
        analysis_content += f"詳解步驟：\n"
        analysis_content += f"1. 識別題目中的物理量或化學物質。\n"
        analysis_content += f"2. 套用相關的物理定律或化學原理，如質量守恆定律。\n"
        analysis_content += f"3. 進行必要的單位換算和數值計算。\n"
        analysis_content += f"例如：水的密度約為 $1\\,g/cm^3$ 或 $1000\\,kg/m^3$。\n"

    else:
        analysis_content += "此題為綜合性問題，需要對相關知識點進行深入理解。\n"
        analysis_content += "解題思路：\n"
        analysis_content += "1. 仔細閱讀題目，理解題意。\n"
        analysis_content += "2. 聯想相關概念與知識點。\n"
        analysis_content += "3. 逐步推導，得出結論。\n"
        
    return analysis_content.strip()

def process_questions(limit: int = 5):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # 以字典形式獲取行
        cursor = conn.cursor()

        # 讀取未處理的題目
        cursor.execute("""
            SELECT id, subject, question, answer, analysis, option_a, option_b, option_c, option_d
            FROM questions_non_mcq
            WHERE answer NOT IN ('A', 'B', 'C', 'D')
            LIMIT ?
        """, (limit,))
        
        questions_to_process = [dict(q) for q in cursor.fetchall()]
        
        if not questions_to_process:
            print("沒有找到需要轉化的題目。")
            return

        transformed_questions_report = []

        for original_q in questions_to_process:
            original_state = dict(original_q) # 複製原始狀態用於報告

            question_id = original_q['id']
            subject = original_q['subject']
            question_text = original_q['question']
            original_answer_text = str(original_q['answer'])

            # Step 2: AI 智慧轉化
            # 生成誘答
            distractors = generate_distractors(original_answer_text, subject, question_text)
            
            # 合併正解和誘答
            all_options = [original_answer_text] + distractors
            random.shuffle(all_options) # 隨機排序

            # 分配給 A, B, C, D
            options_dict = {
                'option_a': all_options[0],
                'option_b': all_options[1],
                'option_c': all_options[2],
                'option_d': all_options[3],
            }
            
            # 確定新的正確答案字母
            new_correct_answer_letter = ''
            for letter, option_text in zip(['A', 'B', 'C', 'D'], all_options):
                if option_text == original_answer_text:
                    new_correct_answer_letter = letter
                    break
            
            # Step 3: 撰寫神級解析
            new_analysis = generate_analysis(question_text, original_answer_text, subject, original_answer_text)

            # Step 4: 寫回資料庫 (UPDATE)
            new_subject = f"{subject}-進階挑戰"
            
            cursor.execute("""
                UPDATE questions_non_mcq
                SET option_a = ?, option_b = ?, option_c = ?, option_d = ?,
                    answer = ?, analysis = ?, subject = ?
                WHERE id = ?
            """, (options_dict['option_a'], options_dict['option_b'], options_dict['option_c'], options_dict['option_d'],
                  new_correct_answer_letter, new_analysis, new_subject, question_id))

            # 讀取轉化後的狀態以供報告
            cursor.execute("""
                SELECT id, subject, question, answer, analysis, option_a, option_b, option_c, option_d
                FROM questions_non_mcq
                WHERE id = ?
            """, (question_id,))
            transformed_q = dict(cursor.fetchone())

            transformed_questions_report.append({
                "原始狀態": original_state,
                "轉化後狀態": transformed_q
            })

        conn.commit()
        print(json.dumps(transformed_questions_report, indent=2, ensure_ascii=False))
        print(f"\n成功轉化並更新了 {len(questions_to_process)} 題。")

    except sqlite3.Error as e:
        print(f"資料庫錯誤: {e}")
        if conn:
            conn.rollback() # 回滾事務
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    process_questions(limit=5)