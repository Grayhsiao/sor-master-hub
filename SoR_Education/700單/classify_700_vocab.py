import json
import os

# Definition of the 14 Chapters
CHAPTERS = {
    1: '從此不再唸錯的英文字母',
    2: '人物篇',
    3: '形容詞',
    4: '顏色',
    5: '數字和限定詞',
    6: '所有格和名詞',
    7: '交通工具和地點方位',
    8: 'Be 動詞、助動詞、動詞',
    9: '興趣愛好',
    10: '時間與節慶',
    11: '天氣和大自然',
    12: '學校',
    13: '其他用字',
    14: '簡單會話'
}

# Load extracted raw data
with open('sor_data_raw.json', 'r') as f:
    words = json.load(f)

# Heuristic Rules
rules = {
    'colors': ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'black', 'white', 'brown', 'pink', 'gray', 'grey', 'color'],
    'numbers': ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'first', 'second', 'third', 'last', 'next', 'many', 'much', 'some', 'any', 'all', 'every', 'each'],
    'people': ['boy', 'girl', 'man', 'woman', 'father', 'mother', 'brother', 'sister', 'teacher', 'student', 'friend', 'doctor', 'nurse', 'baby', 'king', 'queen', 'prince', 'princess'],
    'pronouns': ['i', 'me', 'my', 'mine', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'we', 'us', 'our', 'ours', 'they', 'them', 'their', 'theirs'],
    'transport': ['car', 'bus', 'train', 'bike', 'bicycle', 'plane', 'airplane', 'ship', 'boat', 'truck', 'taxi'],
    'locations': ['home', 'school', 'park', 'room', 'house', 'office', 'bank', 'shop', 'market', 'farm', 'zoo', 'park', 'street', 'road', 'city', 'country', 'place'],
    'prepositions': ['in', 'on', 'at', 'under', 'over', 'by', 'near', 'beside', 'behind', 'front', 'around', 'between', 'among', 'up', 'down', 'left', 'right', 'north', 'south', 'east', 'west'],
    'verbe_aux': ['be', 'is', 'am', 'are', 'was', 'were', 'do', 'does', 'did', 'have', 'has', 'had', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must'],
    'time': ['time', 'day', 'night', 'morning', 'afternoon', 'evening', 'hour', 'minute', 'second', 'week', 'month', 'year', 'today', 'yesterday', 'tomorrow', 'now', 'then', 'before', 'after', 'early', 'late'],
    'festivals': ['christmas', 'new', 'year', 'birthday', 'holiday', 'festival', 'party'],
    'nature': ['sun', 'moon', 'star', 'sky', 'cloud', 'rain', 'snow', 'wind', 'weather', 'hot', 'cold', 'warm', 'cool', 'tree', 'flower', 'leaf', 'grass', 'sea', 'river', 'lake', 'mountain', 'hill', 'earth', 'world'],
    'animals': ['dog', 'cat', 'bird', 'pig', 'cow', 'sheep', 'horse', 'bear', 'lion', 'tiger', 'elephant', 'monkey', 'snake', 'fish', 'ant', 'bee', 'duck', 'chicken'],
    'school': ['teacher', 'student', 'book', 'pen', 'pencil', 'ruler', 'eraser', 'bag', 'test', 'class', 'homework', 'math', 'english', 'art', 'music', 'sport', 'library'],
    'hobbies': ['game', 'sport', 'play', 'sing', 'song', 'dance', 'read', 'write', 'draw', 'paint', 'watch', 'listen', 'swim', 'run', 'jump', 'hop', 'skip'],
    'convo': ['hello', 'hi', 'bye', 'goodbye', 'please', 'thanks', 'thank', 'sorry', 'excuse', 'yes', 'no', 'okay', 'ok', 'welcome']
}

classified = []
ambiguous = []

for w_item in words:
    word = w_item['word'].lower().strip()
    chinese = w_item['chinese']
    pos = w_item['pos'].lower()
    
    proposed_id = None
    reason = ""
    is_ambiguous = False
    possible_chapters = []

    # 1. Alphabet (Ch1)
    if len(word) == 1 or (len(word) == 2 and word.endswith(' ')):
         possible_chapters.append(1)
    
    # 2. Colors (Ch4)
    if any(c in word for c in rules['colors']):
        possible_chapters.append(4)
    
    # 3. Numbers/Determiners (Ch5)
    if any(n in word for n in rules['numbers']):
        possible_chapters.append(5)
    
    # 4. People (Ch2)
    if any(p in word for p in rules['people']):
        possible_chapters.append(2)
    
    # 5. Pronouns (Ch6 Part 1 - Possessives/Nouns)
    if any(pr in word for pr in rules['pronouns']):
        possible_chapters.append(6)
    
    # 6. Transport/Location (Ch7)
    if any(t in word for t in rules['transport']) or any(l in word for l in rules['locations']) or any(prep in word for prep in rules['prepositions']):
        possible_chapters.append(7)

    # 7. Verbs (Ch8)
    if 'v' in pos or any(v in word for v in rules['verbe_aux']):
        possible_chapters.append(8)
    
    # 8. Hobbies (Ch9)
    if any(h in word for h in rules['hobbies']):
        possible_chapters.append(9)
        
    # 9. Time/Festivals (Ch10)
    if any(t in word for t in rules['time']) or any(f in word for f in rules['festivals']):
        possible_chapters.append(10)
        
    # 10. Nature/Animals (Ch11)
    if any(n in word for n in rules['nature']) or any(a in word for a in rules['animals']):
        possible_chapters.append(11)
        
    # 11. School (Ch12)
    if any(s in word for s in rules['school']):
        possible_chapters.append(12)
        
    # 12. Adjectives (Ch3)
    if 'adj' in pos:
        possible_chapters.append(3)
        
    # 13. Conversation (Ch14)
    if any(c in word for c in rules['convo']):
        possible_chapters.append(14)
        
    # Final Decision
    if not possible_chapters:
        proposed_id = 13 # Other (Ch13)
        reason = "No matching rules"
    else:
        # Prioritize more specific ones
        # If both People and Verb, maybe People (Teacher)
        # If both School and Object, School
        unique_chapters = sorted(list(set(possible_chapters)))
        if len(unique_chapters) > 1:
            is_ambiguous = True
            proposed_id = unique_chapters[0] # Take first as guess
            reason = f"Multiple matches: {unique_chapters}"
        else:
            proposed_id = unique_chapters[0]
            reason = "Direct rule match"

    w_item['proposed_chap'] = proposed_id
    w_item['proposed_chap_name'] = CHAPTERS[proposed_id]
    w_item['is_ambiguous'] = is_ambiguous
    w_item['possible_chapters'] = [f"{c}:{CHAPTERS[c]}" for c in possible_chapters]
    w_item['reason'] = reason
    
    classified.append(w_item)
    if is_ambiguous or proposed_id == 13:
        ambiguous.append(w_item)

# Save result
with open('sor_classification_result.json', 'w') as f:
    json.dump(classified, f, ensure_ascii=False, indent=2)

# Generate Ambiguous Report
with open('ambiguous_words.md', 'w') as f:
    f.write("# 🧐 SoR 單字分類疑慮清單 (待確認)\n\n")
    f.write("以下單字可能屬於多個章節，或無法明確歸類，請確認：\n\n")
    f.write("| 單字 | 中文 | 建議章節 | 衝突/原因 |\n")
    f.write("| :--- | :--- | :--- | :--- |\n")
    for item in ambiguous:
        f.write(f"| {item['word']} | {item['chinese']} | {item['proposed_chap_name']} | {item['reason']} |\n")

print(f"Classification done. {len(ambiguous)} ambiguous cases flagged.")
