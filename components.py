css = '''
    <style>
        .search-result {
            padding: 1.5rem; 
            border-radius: 0.5rem; 
            margin-bottom: 1rem; 
            display: flex;
            color: #000000;
            background-color: #9fc5e8
        }
        .chat-message {
            padding: 1.5rem; 
            border-radius: 0.5rem; 
            margin-bottom: 1rem; 
            display: flex
        }
        .chat-message.user {
            background-color: #2b313e
        }
        .chat-message.bot {
            background-color: #475063
        }
        .chat-message.alert-bot {
            background-color: #d63024
        }
        .chat-message .avatar {
        width: 15%;
        }
        .chat-message .avatar img {
        max-width: 78px;
        max-height: 78px;
        border-radius: 50%;
        object-fit: cover;
        }
        .chat-message .message {
        width: 85%;
        padding: 0 1.5rem;
        color: #fff;
        }
'''

header_template = """
    <div style="background-color:#2986cc;padding:10px">
        <h2 style="color:white;text-align:center;">{{MSG}}</h2>
    </div><br>
"""

# function to generate interim orders URLs part of the search result
def generate_interim_orders_info(list_of_interim_order_urls=''):
    if list_of_interim_order_urls:
        html = '<div>List of Interim Order URLs:</div>'
        html += '<ol>'
        for i, url in enumerate(list_of_interim_order_urls):
            html += f'<li><a href="{url}" class="link" target="_blank">View Interim Order {i+1}</a></li>'
        html += '</ol>'
    else:
        html = 'No interim orders available for this case.'

    print("Interim orders:")
    print(html)
    return html

# function to generate judgement URLs part of the search result
def generate_judgement_info(judgement_url=''):
    if judgement_url:
        html = f'<a href="{judgement_url}" class="link" target="_blank">View Judgement</a>'
    else:
        html = 'No judgements available for this case.'

    print("Judgement:")
    print(html)
    print()
    return html

search_result_template = """
    <div class="search-result">
        <div class="info">
            <div class="info-item"><h3>{{CASE_TITLE}}</h3></div>
            <div class="info-item">
                <table>
                    <tr><td><b>Case Type:</b></td><td>{{CASE_TYPE}}</td><td></td><td><b>CNR Number:</b></td><td>{{CNR_NUMBER}}</td></tr>
                </table>
            </div>
            <br>
            <div class="info-item">
                {{INTERIM_ORDERS_URL}}
            </div>
            <div class="info-item">
                {{JUDGEMENT_URL}}
            </div>
        </div>
    </div>
"""

alert_bot_template = '''
    <div class="chat-message alert-bot">
        <div class="avatar">
            <img src="https://www.pngmart.com/files/22/Bot-Angry-Icon-PNG-Photos.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
        </div>
        <div class="message">{{MSG}}</div>
    </div>
'''

bot_template = '''
    <div class="chat-message bot">
        <div class="avatar">
            <img src="https://png.pngtree.com/png-vector/20220622/ourmid/pngtree-chatbot-color-icon-chat-bot-png-image_5258006.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
        </div>
        <div class="message">{{MSG}}</div>
    </div>
'''

user_template = '''
    <div class="chat-message user">
        <div class="avatar">
            <img src="https://static.vecteezy.com/system/resources/thumbnails/002/318/271/small_2x/user-profile-icon-free-vector.jpg">
        </div>    
        <div class="message">{{MSG}}</div>
    </div>
'''