# * @author        TelMovID
# * @date          2025-08-25 10:52:00
# * @projectName   TelMovID
# * Copyright ©TelMovID All rights reserved
import os
import moviepy.editor as mp
from pyrogram import filters
from misskaty import app
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "videorotate"
__HELP__ = """
Command: <code>/rotasi [angle]</code> [reply to video]
Desc: Rotate a video by the specified angle (in degrees, clockwise).
Example: <code>/rotasi 90</code> to rotate 90 degrees clockwise, <code>/rotasi -90</code> for 90 degrees counterclockwise.
Supported angles: Any numerical value (e.g., 90, 180, -90, 45, etc.).
"""

@app.on_message(filters.command(["rotasi"], COMMAND_HANDLER))
async def rotate_video(client, message):
    # Check if the message is a reply to a video file
    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply("Please reply to a video file to rotate.")

    # Get rotation angle
    if len(message.command) < 2 or not message.command[1].lstrip('-').isdigit():
        return await message.reply("Please specify a valid rotation angle in degrees (e.g., /rotasi 90).")
    angle = float(message.command[1])
    
    nan = await message.reply("Processing video rotation...")
    try:
        # Download the video file
        video_file = await client.download_media(message.reply_to_message.video, file_name=f"input_{message.from_user.id}.mp4")
        video = mp.VideoFileClip(video_file)

        # Rotate the video
        output_file = f"rotated_{message.from_user.id}.mp4"
        rotated_video = video.rotate(angle)
        rotated_video.write_videofile(output_file, codec="libx264")

        # Send rotated video
        await message.reply_video(
            video=output_file,
            caption=f"<b>Rotated By:</b> {client.me.mention} (Angle: {angle}°)"
        )

        # Cleanup
        video.close()
        rotated_video.close()
        for file in [video_file, output_file]:
            if os.path.exists(file):
                os.remove(file)
        await nan.delete()

    except Exception as e:
        await nan.delete()
        if os.path.exists(video_file):
            os.remove(video_file)
        return await message.reply(f"Error rotating video: {str(e)}")
