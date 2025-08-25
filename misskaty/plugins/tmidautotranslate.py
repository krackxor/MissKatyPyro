# * @author        TelMovID
# * @date          2025-08-25 10:38:00
# * @projectName   TelMovID
# * Copyright ©TelMovID All rights reserved
import os
import re
from pyrogram import filters
from easygoogletranslate import EasyGoogleTranslate
from misskaty import app
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "autotranslate"
__HELP__ = """
Command: <code>/autotrans [language_code]</code> [reply to .srt file]
Desc: Automatically translate an SRT subtitle file into the specified language.
Example: <code>/autotrans id</code> for Indonesian, <code>/autotrans en</code> for English.
Supported languages: Any valid Google Translate language code (e.g., id, en, es, fr, etc.).
"""

def parse_srt(content):
    # Split SRT content into subtitle blocks
    blocks = content.strip().split("\n\n")
    parsed = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3 and re.match(r"^\d+$", lines[0]) and "-->" in lines[1]:
            index = lines[0]
            timing = lines[1]
            text = "\n".join(lines[2:])
            parsed.append((index, timing, text))
    return parsed

def create_srt(translated_blocks):
    srt_content = ""
    for index, timing, text in translated_blocks:
        srt_content += f"{index}\n{timing}\n{text}\n\n"
    return srt_content

@app.on_message(filters.command(["autotrans"], COMMAND_HANDLER))
async def translate_subtitle(client, message):
    # Check if the message is a reply to an SRT file
    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith(".srt"):
        return await message.reply("Please reply to an .srt subtitle file to translate.")

    # Get language code from command (default to 'en' if not specified)
    lang_code = message.command[1] if len(message.command) > 1 else "en"
    
    nan = await message.reply("Processing subtitle translation...")
    try:
        # Download the SRT file
        srt_file = await client.download_media(message.reply_to_message.document, file_name=f"input_{message.from_user.id}.srt")
        
        # Read and parse the SRT file
        with open(srt_file, "r", encoding="utf-8") as f:
            srt_content = f.read()

        parsed_blocks = parse_srt(srt_content)
        if not parsed_blocks:
            raise ValueError("Invalid or empty SRT file.")

        # Initialize translator
        translator = EasyGoogleTranslate(target_language=lang_code)
        translated_blocks = []

        # Translate each subtitle block
        for index, timing, text in parsed_blocks:
            translated_text = translator.translate(text)
            if not translated_text:
                translated_text = "[Translation failed]"
            translated_blocks.append((index, timing, translated_text))

        # Generate translated SRT file
        translated_srt_content = create_srt(translated_blocks)
        output_file = f"translated_{message.from_user.id}.srt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(translated_srt_content)

        # Send translated SRT file
        await message.reply_document(
            document=output_file,
            caption=f"<b>Translated Subtitles By:</b> {client.me.mention} (Language: {lang_code})"
        )

        # Cleanup
        for file in [srt_file, output_file]:
            if os.path.exists(file):
                os.remove(file)
        await nan.delete()

    except Exception as e:
        await nan.delete()
        return await message.reply(f"Error translating subtitles: {str(e)}")
