# * @author        TelMovID
# * @date          2025-08-25 11:00:00
# * @projectName   TelMovID
# * Copyright ©TelMovID All rights reserved
import os
import moviepy.editor as mp
import subprocess
from pyrogram import filters
from misskaty import app
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "extractmedia"
__HELP__ = """
Command: <code>/extract [type] [options]</code> [reply to video]
Desc: Extract audio, subtitles, or frames from a video file.
Supported types:
- <code>audio</code>: Extract audio as MP3.
- <code>subtitle</code>: Extract embedded subtitles as SRT (if available).
- <code>frame [options]</code>: Extract frame(s) as JPG.
  Options for frame:
  - <code>single [time]</code>: Extract a single frame at specified time (in seconds, e.g., /extract frame single 10).
  - <code>multiple [count]</code>: Extract multiple frames evenly spaced (e.g., /extract frame multiple 5 for 5 frames).
  - No options: Extract a single frame at the midpoint.
Example: <code>/extract audio</code>, <code>/extract subtitle</code>, <code>/extract frame single 10</code>, <code>/extract frame multiple 5</code>
"""

@app.on_message(filters.command(["extract"], COMMAND_HANDLER))
async def extract_media(client, message):
    # Check if the message is a reply to a video file
    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply("Please reply to a video file to extract content.")

    # Get extraction type
    if len(message.command) < 2 or message.command[1].lower() not in ["audio", "subtitle", "frame"]:
        return await message.reply("Please specify a valid extraction type: audio, subtitle, or frame (e.g., /extract audio).")
    extract_type = message.command[1].lower()
    
    nan = await message.reply(f"Extracting {extract_type}...")
    try:
        # Download the video file
        video_file = await client.download_media(message.reply_to_message.video, file_name=f"input_{message.from_user.id}.mp4")
        video = mp.VideoFileClip(video_file)
        output_files = []

        if extract_type == "audio":
            # Extract audio to MP3
            output_file = f"extracted_{message.from_user.id}.mp3"
            video.audio.write_audiofile(output_file, codec="mp3")
            output_files.append(output_file)
            # Send extracted audio
            await message.reply_audio(
                audio=output_file,
                caption=f"<b>Audio Extracted By:</b> {client.me.mention}"
            )

        elif extract_type == "subtitle":
            # Extract embedded subtitles using ffmpeg
            output_file = f"extracted_{message.from_user.id}.srt"
            try:
                # Check for subtitle streams using ffmpeg
                result = subprocess.run(
                    ["ffmpeg", "-i", video_file],
                    capture_output=True, text=True, check=False
                )
                if "Subtitle" not in result.stderr and "Subtitle" not in result.stdout:
                    raise ValueError("No embedded subtitles found in the video.")
                
                # Extract first subtitle stream to SRT
                subprocess.run(
                    ["ffmpeg", "-i", video_file, "-map", "0:s:0", output_file],
                    check=True, capture_output=True
                )
                output_files.append(output_file)
                # Send extracted subtitle
                await message.reply_document(
                    document=output_file,
                    caption=f"<b>Subtitle Extracted By:</b> {client.me.mention}"
                )
            except subprocess.CalledProcessError:
                raise ValueError("Failed to extract subtitles. Ensure the video contains embedded subtitles.")

        elif extract_type == "frame":
            # Handle frame extraction with options
            if len(message.command) == 2:
                # Default: Extract single frame at midpoint
                output_file = f"extracted_{message.from_user.id}_frame.jpg"
                frame_time = video.duration / 2
                video.save_frame(output_file, t=frame_time)
                output_files.append(output_file)
                await message.reply_photo(
                    photo=output_file,
                    caption=f"<b>Frame Extracted By:</b> {client.me.mention} (at {frame_time:.2f}s)"
                )
            elif len(message.command) >= 4 and message.command[2].lower() == "single":
                # Extract single frame at specified time
                try:
                    frame_time = float(message.command[3])
                    if frame_time < 0 or frame_time > video.duration:
                        raise ValueError("Specified time is out of video duration.")
                    output_file = f"extracted_{message.from_user.id}_frame.jpg"
                    video.save_frame(output_file, t=frame_time)
                    output_files.append(output_file)
                    await message.reply_photo(
                        photo=output_file,
                        caption=f"<b>Frame Extracted By:</b> {client.me.mention} (at {frame_time:.2f}s)"
                    )
                except ValueError as e:
                    raise ValueError(f"Invalid time format or value: {str(e)}")
            elif len(message.command) >= 4 and message.command[2].lower() == "multiple":
                # Extract multiple frames
                try:
                    count = int(message.command[3])
                    if count <= 0 or count > 50:  # Limit to 50 frames to avoid abuse
                        raise ValueError("Frame count must be between 1 and 50.")
                    step = video.duration / count
                    for i in range(count):
                        frame_time = i * step
                        output_file = f"extracted_{message.from_user.id}_frame_{i+1}.jpg"
                        video.save_frame(output_file, t=frame_time)
                        output_files.append(output_file)
                        await message.reply_photo(
                            photo=output_file,
                            caption=f"<b>Frame {i+1} Extracted By:</b> {client.me.mention} (at {frame_time:.2f}s)"
                        )
                except ValueError as e:
                    raise ValueError(f"Invalid frame count: {str(e)}")
            else:
                raise ValueError("Invalid frame option. Use: single [time] or multiple [count]")

        # Cleanup
        video.close()
        for file in [video_file] + output_files:
            if os.path.exists(file):
                os.remove(file)
        await nan.delete()

    except Exception as e:
        await nan.delete()
        if os.path.exists(video_file):
            os.remove(video_file)
        return await message.reply(f"Error extracting {extract_type}: {str(e)}")
