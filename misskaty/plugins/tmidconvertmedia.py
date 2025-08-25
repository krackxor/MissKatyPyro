# * @author        TelMovID
# * @date          2025-08-25 10:56:00
# * @projectName   TelMovID
# * Copyright ©TelMovID All rights reserved
import os
import moviepy.editor as mp
from pyrogram import filters
from misskaty import app
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "convertmedia"
__HELP__ = """
Command: <code>/convert [format]</code> [reply to video/audio]
Desc: Convert a video or audio file to MP4 or MP3 format.
Supported formats: mp4, mp3
Example: <code>/convert mp4</code> to convert to MP4, <code>/convert mp3</code> to convert to MP3.
"""

@app.on_message(filters.command(["convert"], COMMAND_HANDLER))
async def convert_media(client, message):
    # Check if the message is a reply to a video or audio file
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.audio):
        return await message.reply("Please reply to a video or audio file to convert.")

    # Get target format
    if len(message.command) < 2 or message.command[1].lower() not in ["mp4", "mp3"]:
        return await message.reply("Please specify a valid format: mp4 or mp3 (e.g., /convert mp4).")
    target_format = message.command[1].lower()
    
    nan = await message.reply(f"Converting to {target_format.upper()}...")
    try:
        # Download the media file
        media = message.reply_to_message.video or message.reply_to_message.audio
        input_file = await client.download_media(media, file_name=f"input_{message.from_user.id}.{media.file_name.split('.')[-1]}")
        
        output_file = f"converted_{message.from_user.id}.{target_format}"
        
        if target_format == "mp4":
            # Convert to MP4 (video or audio to video)
            video = mp.VideoFileClip(input_file) if media.video else mp.AudioFileClip(input_file).to_videoclip(fps=24, duration=media.duration)
            video.write_videofile(output_file, codec="libx264", audio_codec="aac")
            video.close()
            # Send converted video
            await message.reply_video(
                video=output_file,
                caption=f"<b>Converted to MP4 By:</b> {client.me.mention}"
            )
        
        elif target_format == "mp3":
            # Convert to MP3
            audio = mp.AudioFileClip(input_file) if media.video else mp.AudioFileClip(input_file)
            audio.write_audiofile(output_file, codec="mp3")
            audio.close()
            # Send converted audio
            await message.reply_audio(
                audio=output_file,
                caption=f"<b>Converted to MP3 By:</b> {client.me.mention}"
            )

        # Cleanup
        for file in [input_file, output_file]:
            if os.path.exists(file):
                os.remove(file)
        await nan.delete()

    except Exception as e:
        await nan.delete()
        if os.path.exists(input_file):
            os.remove(input_file)
        return await message.reply(f"Error converting media: {str(e)}")
