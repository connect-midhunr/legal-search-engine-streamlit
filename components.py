css = '''
<style>
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
</div><br><br>
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