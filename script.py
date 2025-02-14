# script.py
from enum import Enum

class Language(Enum):
    EN = "en"
    TA = "ta"
    HI = "hi"

# English Messages
messages_en = {
    "welcome": "Welcome to our advanced Crocodile Game Bot! 🐊\n\nGet ready to have fun and challenge your friends!",
    "game_started": "{name}, the game has started! 🎉 Game mode: {mode}, Language: {lang}",
    "new_game_started": "A new game has started!",
    "failed_to_start_game": "Failed to start the new game. Please try again.",
    "game_ended": "The game has been ended.",
    "game_ended_confirmation": "The game has been successfully ended.",
    "not_leader": "You are not the leader. You cannot end the game.",
    "no_game_ongoing": "There is no game ongoing to end.",
    "error_ending_game": "An error occurred while trying to end the game. Please try again.",
    "game_already_started": "The game has already started! Do not blabber. 🤯",
    "settings_option": "Choose an option:",
    "error_registering_chat": "An error occurred while registering the chat. Please try again.",
    "ping": "Pong! 🏓 The bot is alive and responding!",
    "alive": "I am alive! 🤖",
    "provide_message": "Please provide a message to broadcast.",
    "broadcast_pm_success": "Broadcast completed! Total: {total}, Success: {success}, Failed: {failed}, Pending: {pending}.",
    "broadcast_group_success": "Group broadcast completed! Total: {total}, Success: {success}, Failed: {failed}, Pending: {pending}.",
    "stats": "User Count: {user_count}, Chat Count: {chat_count}, Game Count: {game_count}.",
    "game_mode_set": "Game mode has been set to {mode}.",
    "invalid_mode": "Invalid game mode selected. Please choose from Easy, Hard, or Adult.",
    "language_set": "Group language has been set to {language}.",
    "back": "Going back to the previous menu.",
    "close": "The menu has been closed.",
    "current_word": "The current word is: {word} (Game Mode: {mode})",
    "new_word": "The new word is: {word} (Game Mode: {mode})",
    "word_not_updated": "Failed to update the word. Please try again.",
    "database_error": "A database error occurred. Please try again later.",
    "dont_tell_answer": "Hey! Don't tell the answer! Let others have a chance to guess. 😉",
    "correct_answer": "🎉 Congratulations, {winner}! You've guessed the word correctly!",
}

# Tamil Messages
messages_ta = {
    "welcome": "எங்கள் முன்னணி குருட்டு விளையாட்டு பாட்டுக்கு வரவேற்கிறோம்! 🐊\n\nஉங்கள் நண்பர்களை சவால் செய்ய தயாராகுங்கள்!",
    "game_started": "{name}, விளையாட்டு தொடங்கியுள்ளது! 🎉 விளையாட்டு முறை: {mode}, மொழி: {lang}",
    "new_game_started": "புதிய விளையாட்டு தொடங்கியுள்ளது!",
    "failed_to_start_game": "புதிய விளையாட்டை தொடங்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "game_ended": "விளையாட்டு முடிக்கப்பட்டது.",
    "game_ended_confirmation": "விளையாட்டு வெற்றிகரமாக முடிக்கப்பட்டது.",
    "not_leader": "நீங்கள் தலைவரல்ல. நீங்கள் விளையாட்டை முடிக்க முடியாது.",
    "no_game_ongoing": "முடிக்க விளையாட்டு இல்லை.",
    "error_ending_game": "விளையாட்டை முடிக்க முயற்சிக்கும் போது பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "game_already_started": "விளையாட்டு ஏற்கனவே தொடங்கியுள்ளது! பேச வேண்டாம். 🤯",
    "settings_option": "ஒரு விருப்பத்தை தேர்ந்தெடுக்கவும்:",
    "error_registering_chat": "சாட் பதிவு செய்யும்போது பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "ping": "பாங்! 🏓 பாட்டி உயிருடன் உள்ளது மற்றும் பதிலளிக்கிறது!",
    "alive": "நான் உயிருடன் இருக்கிறேன்! 🤖",
    "provide_message": "பிரசுரிக்க ஒரு செய்தியை வழங்கவும்.",
    "broadcast_pm_success": "பிரசுரிப்பு முடிந்தது! மொத்தம்: {total}, வெற்றி: {success}, தோல்வி: {failed}, நிலுவையில்: {pending}.",
    "broadcast_group_success": "குழு பிரசுரிப்பு முடிந்தது! மொத்தம்: {total}, வெற்றி: {success}, தோல்வி: {failed}, நிலுவையில்: {pending}.",
    "game_mode_set": "விளையாட்டு முறை {mode} ஆக அமைக்கப்பட்டுள்ளது.",
    "invalid_mode": "தவறான விளையாட்டு முறை தேர்ந்தெடுக்கப்பட்டுள்ளது. தயவுசெய்து எளிதான, கடினமான அல்லது பெரியவனாக தேர்ந்தெடுக்கவும்.",
    "language_set": "குழு மொழி {language} ஆக அமைக்கப்பட்டுள்ளது.",
    "back": "முந்தைய மெனுவுக்கு திரும்புகிறேன்.",
    "close": "மெனு மூடப்பட்டுள்ளது.",
    "current_word": "தற்போதைய சொல்: {word} (விளையாட்டு முறை: {mode})",
    "new_word": "புதிய சொல்: {word} (விளையாட்டு முறை: {mode})",
    "word_not_updated": "சொல்லைப் புதுப்பிக்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "database_error": "ஒரு தரவுத்தள பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "dont_tell_answer": "ஏய்! பதில சொல்லாதீங்க! மற்றவர்கள் யூகிக்க ஒரு வாய்ப்பு கொடுங்க. 😉",
    "correct_answer": "🎉 வாழ்த்துக்கள், {winner}! நீங்கள் சொல்லை சரியாக யூகித்துவிட்டீர்கள்!",
}

# Hindi Messages
messages_hi = {
    "welcome": "हमारे उन्नत मगरमच्छ खेल बॉट में आपका स्वागत है! 🐊\n\nमज़े करने और अपने दोस्तों को चुनौती देने के लिए तैयार हो जाइए!",
    "game_started": "{name}, खेल शुरू हो गया है! 🎉 खेल मोड: {mode}, भाषा: {lang}",
    "new_game_started": "एक नया खेल शुरू हो गया है!",
    "failed_to_start_game": "नया खेल शुरू करने में विफल। कृपया पुनः प्रयास करें।",
    "game_ended": "खेल समाप्त हो गया है।",
    "game_ended_confirmation": "खेल सफलतापूर्वक समाप्त हो गया है।",
    "not_leader": "आप नेता नहीं हैं। आप खेल समाप्त नहीं कर सकते।",
    "no_game_ongoing": "कोई खेल चल रहा नहीं है जिसे समाप्त किया जा सके।",
    "error_ending_game": "खेल समाप्त करने का प्रयास करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
    "game_already_started": "खेल पहले से ही शुरू हो चुका है! बकवास मत करो। 🤯",
    "settings_option": "एक विकल्प चुनें:",
    "error_registering_chat": "चैट को पंजीकृत करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
    "ping": "पोंग! 🏓 बॉट जीवित है और प्रतिक्रिया दे रहा है!",
    "alive": "मैं जीवित हूँ! 🤖",
    "provide_message": "कृपया प्रसारण के लिए एक संदेश प्रदान करें।",
    "broadcast_pm_success": "प्रसारण पूरा हुआ! कुल: {total}, सफल: {success}, विफल: {failed}, लंबित: {pending}.",
    "broadcast_group_success": "समूह प्रसारण पूरा हुआ! कुल: {total}, सफल: {success}, विफल: {failed}, लंबित: {pending}.",
    "stats": "उपयोगकर्ता संख्या: {user_count}, चैट संख्या: {chat_count}, खेल संख्या: {game_count}.",
    "game_mode_set": "खेल मोड {mode} पर सेट किया गया है।",
    "invalid_mode": "अमान्य खेल मोड चुना गया है। कृपया आसान, कठिन, या वयस्क में से चुनें।",
    "language_set": "समूह भाषा {language} पर सेट की गई है।",
    "back": "पिछले मेनू में वापस जा रहा हूँ।",
    "close": "मेनू बंद कर दिया गया है।",
    "current_word": "वर्तमान शब्द है: {word} (खेल मोड: {mode})",
    "new_word": "नया शब्द है: {word} (खेल मोड: {mode})",
    "word_not_updated": "शब्द को अपडेट करने में विफल। कृपया पुनः प्रयास करें।",
    "database_error": "एक डेटाबेस त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।",
    "dont_tell_answer": "अरे! जवाब मत बताओ! दूसरों को अनुमान लगाने का मौका दो। 😉",  # Corrected
    "correct_answer": "🎉 बधाई हो, {winner}! आपने शब्द का सही अनुमान लगाया है!",  # Corrected
}
messages = {
    Language.EN: messages_en,
    Language.TA: messages_ta,
    Language.HI: messages_hi
}
