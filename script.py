# script.py

# Function to handle language retrieval
def get_user_language(user_language):
    return user_language if user_language in ["en", "ta", "hi"] else "en"  # Fallback to English if not set

# English Messages
messages_en = {
    "welcome": "Welcome to our advanced Crocodile Game Bot! 🐊\n\nGet ready to have fun and challenge your friends!",
    "game_started": "{name}, the game has started! 🎉",
    "new_game_started": "A new game has started!",
    "failed_to_start_game": "Failed to start the new game. Please try again.",
    "game_ended": "The game has been ended.",
    "game_ended_confirmation": "The game has been successfully ended.",
    "not_leader": "You are not the leader. You cannot end the game.",
    "no_game_ongoing": "There is no game ongoing to end.",
    "error_ending_game": "An error occurred while trying to end the game. Please try again.",
    "game_already_started": "The game has already started! Do not blabber. 🤯",
    "settings_option": "Choose an option:",
    "error_registering_user": "An error occurred while registering the user. Please try again.",
    "error_registering_chat": "An error occurred while registering the chat. Please try again.",
    "ping": "Pong! 🏓 The bot is alive and responding!",
    "alive": "I am alive! 🤖",
    "provide_message": "Please provide a message to broadcast.",
    "broadcast_pm_success": "Broadcast completed! Total: {total}, Success: {success}, Failed: {failed}, Pending: {pending}.",
    "broadcast_group_success": "Group broadcast completed! Total: {total}, Success: {success}, Failed: {failed}, Pending: {pending}.",
    "stats": "User  Count: {user_count}, Chat Count: {chat_count}, Game Count: {game_count}.",
}

# Tamil Messages
messages_ta = {
    "welcome": "எங்கள் முன்னணி குருட்டு விளையாட்டு பாட்டுக்கு வரவேற்கிறோம்! 🐊\n\nஉங்கள் நண்பர்களை சவால் செய்ய தயாராகுங்கள்!",
    "game_started": "{name}, விளையாட்டு தொடங்கியுள்ளது! 🎉",
    "new_game_started": "புதிய விளையாட்டு தொடங்கியுள்ளது!",
    "failed_to_start_game": "புதிய விளையாட்டை தொடங்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "game_ended": "விளையாட்டு முடிக்கப்பட்டது.",
    "game_ended_confirmation": "விளையாட்டு வெற்றிகரமாக முடிக்கப்பட்டது.",
    "not_leader": "நீங்கள் தலைவரல்ல. நீங்கள் விளையாட்டை முடிக்க முடியாது.",
    "no_game_ongoing": "முடிக்க விளையாட்டு இல்லை.",
    "error_ending_game": "விளையாட்டை முடிக்க முயற்சிக்கும் போது பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "game_already_started": "விளையாட்டு ஏற்கனவே தொடங்கியுள்ளது! பேச வேண்டாம். 🤯",
    "settings_option": "ஒரு விருப்பத்தை தேர்ந்தெடுக்கவும்:",
    "error_registering_user": "பயனரை பதிவு செய்யும்போது பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "error_registering_chat": "சாட் பதிவு செய்யும்போது பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "ping": "பாங்! 🏓 பாட்டி உயிருடன் உள்ளது மற்றும் பதிலளிக்கிறது!",
    "alive": "நான் உயிருடன் இருக்கிறேன்! 🤖",
    "provide_message": "பிரசுரிக்க ஒரு செய்தியை வழங்கவும்.",
    "broadcast_pm_success": "பிரசுரிப்பு முடிந்தது! மொத்தம்: {total}, வெற்றி: {success}, தோல்வி: {failed}, நிலுவையில்: {pending}.",
    "broadcast_group_success": "குழு பிரசுரிப்பு முடிந்தது! மொத்தம்: {total}, வெற்றி: {success}, தோல்வி: {failed}, நிலுவையில்: {pending}.",
    "stats": "பயனர் எண்ணிக்கை: {user_count}, சாட் எண்ணிக்கை: {chat_count}, விளையாட்டு எண்ணிக்கை: {game_count}.",
}

# Hindi Messages
messages_hi = {
    "welcome": "हमारे उन्नत मगरमच्छ खेल बॉट में आपका स्वागत है! 🐊\n\nमज़े करने और अपने दोस्तों को चुनौती देने के लिए तैयार हो जाइए!",
    "game_started": "{name}, खेल शुरू हो गया है! 🎉",
    "new_game_started": "एक नया खेल शुरू हो गया है!",
    "failed_to_start_game": "नया खेल शुरू करने में विफल। कृपया पुनः प्रयास करें।",
    "game_ended": "खेल समाप्त हो गया है।",
    "game_ended_confirmation": "खेल सफलतापूर्वक समाप्त हो गया है।",
    "not_leader": "आप नेता नहीं हैं। आप खेल समाप्त नहीं कर सकते।",
    "no_game_ongoing": "कोई खेल चल रहा नहीं है जिसे समाप्त किया जा सके।",
    "error_ending_game": "खेल समाप्त करने का प्रयास करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
    "game_already_started": "खेल पहले से ही शुरू हो चुका है! बकवास मत करो। 🤯",
    "settings_option": "एक विकल्प चुनें:",
    "error_registering_user": "उपयोगकर्ता को पंजीकृत करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
    "error_registering_chat": "चैट को पंजीकृत करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
    "ping": "पोंग! 🏓 बॉट जीवित है और प्रतिक्रिया दे रहा है!",
    "alive": "मैं जीवित हूँ! 🤖",
    "provide_message": "कृपया प्रसारण के लिए एक संदेश प्रदान करें।",
    "broadcast_pm_success": "प्रसारण पूरा हुआ! कुल: {total}, सफल: {success}, विफल: {failed}, लंबित: {pending}.",
    "broadcast_group_success": "समूह प्रसारण पूरा हुआ! कुल: {total}, सफल: {success}, विफल: {failed}, लंबित: {pending}.",
    "stats": "उपयोगकर्ता संख्या: {user_count}, चैट संख्या: {chat_count}, खेल संख्या: {game_count}.",
}
