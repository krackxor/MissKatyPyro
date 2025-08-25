# * @author        TelMovID
# * @date          2025-08-25 11:04:00
# * @projectName   TelMovID
# * Copyright ©TelMovID All rights reserved
import os
import json
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from pyrogram import filters
from misskaty import app
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "editmetadata"
__HELP__ = """
Command: <code>/metadata [json_data]</code> [reply to video/audio]
Desc: Edit metadata of a video or audio file using a JSON string.
Supported formats: Video (e.g., MP4), Audio (e.g., MP3).
JSON format example: 
<code>{"title": "My Song", "artist": "Artist Name", "album": "Album Name", "year": "2023", "genre": "Pop", "comment": "My Comment"}</code>
Supported metadata fields: title, artist, album, year, genre, comment, or any valid field for the file format.
Example: <code>/metadata {"title": "New Title", "artist": "New Artist"}</code>
Note: Reply to a video/audio file and provide metadata as a JSON string.
"""

@app.on_message(filters.command(["metadata"], COMMAND_HANDLER))
async def edit_metadata(client, message):
    # Check if the message is a reply to a video or audio file
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.audio):
        return await message.reply("Please reply to a video or audio file to edit metadata.")

    # Get JSON metadata
    if len(message.command) < 2:
        return await message.reply("Please provide metadata as a JSON string (e.g., /metadata {\"title\": \"New Title\"}).")
    
    try:
        metadata = json.loads(" ".join(message.command[1:]))
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a valid JSON object.")
    except json.JSONDecodeError:
        return await message.reply("Invalid JSON format. Please provide valid JSON (e.g., {\"title\": \"New Title\"}).")
    
    nan = await message.reply("Processing metadata update...")
    try:
        # Download the media file
        media = message.reply_to_message.video or message.reply_to_message.audio
        input_file = await client.download_media(media, file_name=f"input_{message.from_user.id}.{media.file_name.split('.')[-1]}")
        output_file = f"output_{message.from_user.id}.{media.file_name.split('.')[-1]}"

        # Copy the input file to output to preserve content
        os.system(f"cp {input_file} {output_file}")

        # Handle metadata based on file type
        file_ext = media.file_name.split('.')[-1].lower()
        if file_ext in ["mp4", "m4a", "m4v"]:
            # Handle MP4-based files
            mp4_file = MP4(output_file)
            mp4_tags = {
                "title": "\xa9nam",
                "artist": "\xa9ART",
                "album": "\xa9alb",
                "year": "\xa9day",
                "genre": "\xa9gen",
                "comment": "\xa9cmt"
            }
            for key, value in metadata.items():
                tag_key = mp4_tags.get(key, key)  # Use provided key if not in mapping
                mp4_file[tag_key] = str(value)
            mp4_file.save()
        elif file_ext == "mp3":
            # Handle MP3 files with EasyID3 for simplicity
            mp3_file = MP3(output_file, ID3=EasyID3)
            for key, value in metadata.items():
                mp3_file[key] = str(value)
            mp3_file.save()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: mp4, mp3.")

        # Send the modified file
        if media.video:
            await message.reply_video(
                video=output_file,
                caption=f"<b>Metadata Updated By:</b> {client.me.mention}\n<b>Updated Fields:</b> {', '.join(metadata.keys())}"
            )
        else:
            await message.reply_audio(
                audio=output_file,
                caption=f"<b>Metadata Updated By:</b> {client.me.mention}\n<b>Updated Fields:</b> {', '.join(metadata.keys())}"
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
        if os.path.exists(output_file):
            os.remove(output_file)
        return await message.reply(f"Error updating metadata: {str(e)}")
