from datetime import datetime
import re
from prize_manager import prize_manager
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, 
    TextComponent, ButtonComponent, SeparatorComponent, 
    MessageAction
)

class LineHandler:
    @staticmethod
    def parse_message(text):
        """
        解析訊息，例如：
        「早餐 100」-> category="早餐", amount=100
        「100 晚餐」-> category="晚餐", amount=100
        「午餐 150 今天很熱」-> category="午餐", amount=150, note="今天很熱"
        """
        # 尋找數字 (金額)
        amount_match = re.search(r'\d+', text)
        if not amount_match:
            return None
        
        amount = int(amount_match.group())
        
        # 移除數字後的剩餘文字作為類別與備註
        parts = text.replace(str(amount), '').split()
        category = parts[0] if len(parts) > 0 else "未分類"
        note = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "amount": amount,
            "note": note
        }
    @staticmethod
    def get_batch_summary_flex(records):
        """
        生成批次記帳成功的彙總卡片
        """
        count = len(records)
        total = sum(float(r.get('amount', 0)) for r in records)
        
        # 建立前 5 筆預覽
        preview_rows = []
        for r in records[:5]:
            preview_rows.append(
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text=f"• {r.get('category')}", size='xs', color='#888888', flex=1),
                        TextComponent(text=f"{r.get('amount')}元", size='xs', color='#555555', align='end', flex=2)
                    ]
                )
            )
        if count > 5:
            preview_rows.append(TextComponent(text=f"...以及其他 {count-5} 筆交易", size='xxs', color='#AAAAAA', align='center', margin='sm'))

        bubble = BubbleContainer(
            direction='ltr',
            header=BoxComponent(
                layout='vertical',
                background_color='#FFB2B2',
                padding_all='20px',
                contents=[
                    TextComponent(text='📝 批次記帳成功 📝', weight='bold', size='md', color='#ffffff', align='center')
                ]
            ),
            body=BoxComponent(
                layout='vertical',
                padding_all='20px',
                contents=[
                    TextComponent(text='總計匯入筆數', size='xs', color='#AAAAAA', align='center'),
                    TextComponent(text=f'{count} 筆', weight='bold', size='xl', color='#FF6B6B', align='center', margin='xs'),
                    TextComponent(text=f'總金額：NT$ {total}', size='sm', color='#FF8888', align='center', margin='xs'),
                    SeparatorComponent(margin='xl', color='#FFEEEE'),
                    TextComponent(text='資料預覽：', size='xs', weight='bold', margin='md', color='#888888'),
                    BoxComponent(
                        layout='vertical',
                        margin='sm',
                        spacing='xs',
                        contents=preview_rows
                    )
                ]
            ),
            footer=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='已成功同步至 Google Sheets！✨', size='xxs', color='#FFB2B2', align='center', margin='md')
                ]
            )
        )
        return FlexSendMessage(alt_text=f"📝 批次記帳成功！共 {count} 筆", contents=bubble)

    @staticmethod
    def get_summary_flex(summary_data):
        """
        生成統計報表的 Flex Message
        """
        title = summary_data.get('title', '消費月報')
        month = summary_data.get('month')
        total = summary_data.get('total')
        count = summary_data.get('count')
        cat_details = summary_data.get('category_details', {})

        # 建立類別按鈕列表
        cat_rows = []
        for cat, amt in cat_details.items():
            cat_rows.append(
                ButtonComponent(
                    action=MessageAction(label=f"{cat}: {amt} 元", text=f"類別細目:{cat}"),
                    style='secondary',
                    color='#F0F0F0',
                    margin='xs',
                    height='sm'
                )
            )

        bubble = BubbleContainer(
            direction='ltr',
            header=BoxComponent(
                layout='vertical',
                background_color='#1DB446',
                contents=[
                    TextComponent(text=title, weight='bold', size='lg', color='#ffffff', align='center')
                ]
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='總支出金額', size='xs', color='#AAAAAA', align='center'),
                    TextComponent(text=f'NT$ {total}', weight='bold', size='xxl', margin='md', align='center', color='#1DB446'),
                    
                    # 預算進度條
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        contents=[
                            BoxComponent(
                                layout='horizontal',
                                contents=[
                                    TextComponent(text='預算進度', size='xs', color='#888888', flex=1),
                                    TextComponent(text=f'{int((total/summary_data.get("budget", 1))*100)}%', size='xs', color='#888888', align='end', flex=1)
                                ]
                            ),
                            BoxComponent(
                                layout='vertical',
                                margin='sm',
                                background_color='#EEEEEE',
                                height='6px',
                                border_radius='3px',
                                contents=[
                                    BoxComponent(
                                        layout='vertical',
                                        width=f'{min(100, int((total/summary_data.get("budget", 1))*100))}%',
                                        background_color='#1DB446' if total <= summary_data.get('budget', 0) else '#FF6B6B',
                                        height='6px',
                                        border_radius='3px',
                                        contents=[]
                                    )
                                ]
                            ),
                            TextComponent(text=f'剩餘：NT$ {summary_data.get("remaining")}', size='xxs', color='#AAAAAA', margin='xs', align='end')
                        ]
                    ),

                    SeparatorComponent(margin='xl'),
                    TextComponent(text='類別統計 (點擊看明細)', size='sm', weight='bold', margin='lg', color='#555555'),
                    BoxComponent(
                        layout='vertical',
                        margin='md',
                        spacing='xs',
                        contents=cat_rows
                    ),
                    SeparatorComponent(margin='xl'),
                    BoxComponent(
                        layout='horizontal',
                        margin='md',
                        contents=[
                            TextComponent(text='總計筆數', size='xs', color='#AAAAAA', flex=1),
                            TextComponent(text=f'{count} 筆', size='xs', color='#AAAAAA', align='end', flex=4)
                        ]
                    )
                ]
            ),
            footer=BoxComponent(
                layout='vertical',
                contents=[
                    SeparatorComponent(margin='md'),
                    ButtonComponent(
                        action=MessageAction(
                            label='查看詳細明細' if '家庭' not in title else '查看全家明細', 
                            text='詳細報表' if '家庭' not in title else '家庭明細'
                        ),
                        style='link',
                        color='#1DB446',
                        height='sm'
                    )
                ]
            )
        )
        return FlexSendMessage(alt_text=f"{month} 消費月報", contents=bubble)

    @staticmethod
    def get_detailed_list_flex(summary_data, filter_category=None):
        """
        生成交易清單，支援選用特定類別篩選
        """
        title = summary_data.get('title', '消費細目')
        items = summary_data.get('items', [])
        
        # 篩選類別
        if filter_category:
            items = [it for it in items if it.get('category') == filter_category]
            display_title = f"{filter_category} 支出細目"
        else:
            display_title = title

        # 只顯示最近的 20 筆
        display_items = items[-20:]
        
        item_rows = []
        for it in display_items:
            # 格式化日期只取日
            short_date = it.get('date', '').split(' ')[0].split('-')[-1] + "日"
            item_rows.append(
                BoxComponent(
                    layout='horizontal',
                    margin='sm',
                    contents=[
                        TextComponent(text=short_date, size='xs', color='#AAAAAA', flex=1),
                        TextComponent(text=it.get('category'), size='sm', color='#555555', flex=2),
                        TextComponent(text=f"{it.get('amount')}元", size='sm', color='#111111', align='end', flex=2)
                    ]
                )
            )

        bubble = BubbleContainer(
            direction='ltr',
            header=BoxComponent(
                layout='vertical',
                background_color='#1DB446',
                contents=[
                    TextComponent(text=f"📋 {display_title}", weight='bold', size='md', color='#ffffff', align='center')
                ]
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='編號', size='xs', color='#AAAAAA', flex=1),
                            TextComponent(text='項目', size='xs', color='#AAAAAA', flex=2),
                            TextComponent(text='金額', size='xs', color='#AAAAAA', align='end', flex=2)
                        ]
                    ),
                    SeparatorComponent(margin='sm'),
                    BoxComponent(
                        layout='vertical',
                        margin='md',
                        spacing='sm',
                        contents=item_rows
                    )
                ]
            )
        )
        return FlexSendMessage(alt_text="詳細交易清單", contents=bubble)

    @staticmethod
    def get_flex_message(record):
        """
        將記帳紀錄轉換為超可愛的 Flex Message
        """
        category = record.get('category', '未分類')
        amount = str(record.get('amount', 0))
        note = record.get('note', '')
        date = record.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # 根據金額給予不同的小評價
        try:
            amt_val = float(amount)
            comment = "省錢小達人！✨" if amt_val < 100 else "花錢有理，記帳萬歲！🎈"
        except:
            comment = "花錢有理，記帳萬歲！🎈"

        # 發票對獎邏輯
        invoice_number = record.get('invoice_number', '')
        prize_text = ""
        prize_color = "#AAAAAA"
        if invoice_number and len(invoice_number) == 8:
            is_winner, msg = prize_manager.check_prize(invoice_number, invoice_date=date)
            prize_text = f"🎫 發票號碼：{invoice_number}\n{msg}"
            if is_winner:
                prize_color = "#FF6B6B"
        elif invoice_number:
             prize_text = f"🎫 發票辨識：{invoice_number} (號碼異常)"

        bubble_contents = [
            # 大大圓圓的金額顯示
            BoxComponent(
                layout='vertical',
                background_color='#FFF0F0',
                border_radius='20px',
                padding_all='15px',
                contents=[
                    TextComponent(text=f'NT$ {amount}', weight='bold', size='xxl', color='#FF6B6B', align='center'),
                    TextComponent(text=comment, size='xs', color='#FFAAAA', align='center', margin='sm')
                ]
            )
        ]

        if prize_text:
            bubble_contents.append(
                BoxComponent(
                    layout='vertical',
                    margin='md',
                    background_color='#FDFDFD',
                    padding_all='10px',
                    border_width='1px',
                    border_color='#EEEEEE',
                    border_radius='md',
                    contents=[
                        TextComponent(text=prize_text, size='xs', color=prize_color, wrap=True, align='center')
                    ]
                )
            )

        bubble_contents.append(
            BoxComponent(
                layout='vertical',
                margin='xl',
                spacing='md',
                contents=[
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='🐾 類別', size='sm', color='#888888', flex=1),
                            TextComponent(text=category, size='sm', color='#555555', align='end', flex=4, weight='bold')
                        ]
                    ),
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='📝 備註', size='sm', color='#888888', flex=1),
                            TextComponent(text=note if note else '無', size='sm', color='#555555', align='end', flex=4)
                        ]
                    ),
                    SeparatorComponent(margin='md', color='#FFEEEE'),
                    BoxComponent(
                        layout='horizontal',
                        margin='md',
                        contents=[
                            TextComponent(text='⏰ 時間', size='xs', color='#AAAAAA', flex=1),
                            TextComponent(text=date, size='xs', color='#AAAAAA', align='end', flex=4)
                        ]
                    )
                ]
            )
        )

        bubble = BubbleContainer(
            direction='ltr',
            header=BoxComponent(
                layout='vertical',
                background_color='#FFB2B2',
                padding_all='20px',
                contents=[
                    TextComponent(text='🌸 記帳漂亮成功 🌸', weight='bold', size='md', color='#ffffff', align='center')
                ]
            ),
            body=BoxComponent(
                layout='vertical',
                padding_all='20px',
                contents=bubble_contents
            ),
            footer=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='繼續保持唷！加油！🍰', size='xs', color='#FFB2B2', align='center', margin='md')
                ]
            )
        )
        return FlexSendMessage(alt_text=f"🌸 記帳成功囉！花了 {amount} 元", contents=bubble)
