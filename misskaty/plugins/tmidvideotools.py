# * @author        TelMovID
# * @date          2025-08-25 10:46:00
# * @projectName   TelMovID
# * Copyright ©TelMovID All rights reserved
import os
import moviepy.editor as mp
from pyrogram import filters
from misskaty import app
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "videotools"
__HELP__ = """
Command: <code>/videotools [subcommand] [args]</code> [reply to video]
Desc: Process video files with various tools: cut, split, crop, or autocrop.
Subcommands:
- <code>cut [start] [end]</code>: Cut video from start to end (in seconds, e.g., /videotools cut 10 20).
- <code>split [duration]</code>: Split video into parts of specified duration (in seconds, e.g., /videotools split 30).
- <code>crop [x1] [y1] [x2] [y2]</code>: Crop video to specified rectangle (e.g., /videotools crop 100 100 500 400).
- <code>autocrop</code>: Automatically crop video to remove black borders.
Example: <code>/videotools cut 10 20</code>, <code>/videotools autocrop</code>
"""

@app.on_message(filters.command(["videotools"], COMMAND_HANDLER))
async def video_tools(client, message):
    # Check if the message is a reply to a video file
    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply("Please reply to a video file to process.")

    # Get subcommand and arguments
    if len(message.command) < 2:
        return await message.reply("Please specify a subcommand: cut, split, crop, or autocrop.")
    subcommand = message.command[1].lower()
    
    nan = await message.reply("Processing video...")
    try:
        # Download the video file
        video_file = await client.download_media(message.reply_to_message.video, file_name=f"input_{message.from_user.id}.mp4")
        video = mp.VideoFileClip(video_file)
        output_files = []

        if subcommand == "cut":
            if len(message.command) != 4 or not all(x.isdigit() for x in message.command[2:4]):
                raise ValueError("Usage: /videotools cut [start] [end] (in seconds)")
            start, end = map(int, message.command[2:4])
            if start >= end or end > video.duration:
                raise ValueError("Invalid start or end time.")
            output_file = f"cut_{message.from_user.id}.mp4"
            video.subclip(start, end).write_videofile(output_file, codec="libx264")
            output_files.append(output_file)

        elif subcommand == "split":
            if len(message.command) != 3 or not message.command[2].isdigit():
                raise ValueError("Usage: /videotools split [duration] (in seconds)")
            split_duration = int(message.command[2])
            if split_duration <= 0 or split_duration >= video.duration:
                raise ValueError("Invalid split duration.")
            num_parts = int(video.duration // split_duration) + (1 if video.duration % split_duration else 0)
            for i in range(num_parts):
                start = i * split_duration
                end = min((i + 1) * split_duration, video.duration)
                output_file = f"split_{message.from_user.id}_part{i+1}.mp4"
                video.subclip(start, end).write_videofile(output_file, codec="libx264")
                output_files.append(output_file)

        elif subcommand == "crop":
            if len(message.command) != 6 or not all(x.isdigit() for x in message.command[2:6]):
                raise ValueError("Usage: /videotools crop [x1] [y1] [x2] [y2]")
            x1, y1, x2, y2 = map(int, message.command[2:6])
            if x1 >= x2 or y1 >= y2 or x2 > video.w or y2 > video.h:
                raise ValueError("Invalid crop coordinates.")
            output_file = f"crop_{message.from_user.id}.mp4"
            video.crop(x1=x1, y1=y1, x2=x2, y2=y2).write_videofile(output_file, codec="libx264")
            output_files.append(output_file)

        elif subcommand == "autocrop":
            # Simple auto-crop: detect black borders by analyzing edges
            from moviepy.video.tools.cuts import detect_scenes
            # Convert video to grayscale for edge detection
            gray_video = video.fx(mp.vfx.blackwhite)
            # Detect content boundaries (simplified approach)
            frame = gray_video.get_frame(0)
            from PIL import Image
            import numpy as np
            img = Image.fromarray(frame)
            img_array = np.array(img)
            non_black = np.where(img_array > 30)  # Threshold for non-black pixels
            if non_black[0].size and non_black[1].size:
                y1, y2 = max(0, non_black[0].min()), min(img_array.shape[0], non_black[0].max())
                x1, x2 = max(0, non_black[1].min()), min(img_array.shape[1], non_black[1].max())
                if x1 < x2 and y1 < y2:
                    output_file = f"autocrop_{message.from_user.id}.mp4"
                    video.crop(x1=x1, y1=y1, x2=x2, y2=y2).write_videofile(output_file, codec="libx264")
                    output_files.append(output_file)
                else:
                    raise ValueError("Could not detect valid crop boundaries.")
            else:
                raise ValueError("Could not detect non-black content for auto-crop.")

        else:
            raise ValueError("Invalid subcommand. Use: cut, split, crop, or autocrop.")

        # Send output files
        for output_file in output_files:
            await message.reply_video(
                video=output_file,
                caption=f"<b>Processed By:</b> {client.me.mention} ({subcommand})"
            )

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
        return await message.reply(f"Error processing video: {str(e)}")
