from fastapi import FastAPI, Depends, HTTPException, Response, Query   
from pydantic import BaseModel, Field
import os
import urllib.parse
import httpx
from fastapi_mcp import FastApiMCP
from dotenv import load_dotenv

app = FastAPI(title="ultra-mcp-ss")

load_dotenv()

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


SMARTSCREEN_API_URL = "https://smartscreen.tv/api"
SMARTSCREEN_SERVICE_TOKEN = os.environ.get("SMARTSCREEN_SERVICE_TOKEN")


async def search_youtube_video(query: str) -> str | None:
    """
    Searches YouTube for the most relevant video and returns its ID.
    Returns None if no video is found or an error occurs.
    """
    if not YOUTUBE_API_KEY:
        print("Error: YOUTUBE_API_KEY environment variable not set.")
        return None

    encoded_query = urllib.parse.quote_plus(query)
    params = {
        "part": "snippet",
        "q": encoded_query,
        "key": YOUTUBE_API_KEY,
        "type": "video",
        "maxResults": 1,
        "order": "relevance"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(YOUTUBE_API_URL, params=params)
            response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            
            data = response.json()

            if data.get("items"):
                # Safely get the videoId
                video_id = data["items"][0].get("id", {}).get("videoId")
                return video_id
            else:
                # No results found for the query
                return None

    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        return None
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        print(f"Response body: {exc.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# Pydantic models for input
class DropRequest(BaseModel):
    display: str
    item: str  # the item to drop
    x: int = 0  # coordinate (if applicable)
    y: int = 0  # coordinate (if applicable)

class NotifyRequest(BaseModel):
    display: str
    message: str
    priority: str# = Field(default="normal")

class ToastRequest(BaseModel):
    display: str
    message: str
    heading: str
    icon: str
    transition: str
    duration: str = "5"

class MarqueeRequest(BaseModel):
    display: str
    message: str
    duration: str = "30"
    color: str
    size: str = "3"
    bgcolor: str

class TextRequest(BaseModel):
    display: str
    message: str
    duration: str = "30"
    color: str
    size: str = "3"
    bgcolor: str
    align: str
    frame: str
    animate: str
    aniduration: str = "2"

class AppRequest(BaseModel):
    display: str
    url: str
    duration: str = "0"
    frame: str

class TouchRequest(BaseModel):
    display: str
    option: str
    value: str# = ""

class StatusRequest(BaseModel):
    display: str
    option: str
    value: str# = ""

class DjRequest(BaseModel):
    display: str
    option: str
    value: str


class SmartScreenClient:
    """
    Client for calling the real SmartScreen API.
    
    It sends a POST request to the SmartScreen API endpoint with a payload containing:
      - 'to': { "ddn": "yview" } (using yview as the destination target)
      - 'data': (a command JSON as specified)
    
    It uses httpx in async mode.
    """
    def __init__(self):
        self.api_url = SMARTSCREEN_API_URL
        self.token = SMARTSCREEN_SERVICE_TOKEN

    async def drop(self, item: str, display: str, x: int, y: int) -> bool:
        # Construct the command payload for "drop"
        command = {
            "cmd": "drop",
            "type": "url",
            "src": [item],  # Use the passed URL instead of hardcoded one
            "duration": "0",    # 0 means play to end
            "frame": "main",
            "animate": "fade",
            "aniduration": "2",
            "pmode": "loop",
            "bgcolor": "white"
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"  # Use class variable instead of hardcoded token
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            # Check for HTTP success (200 OK)
            if response.status_code != 200:
                print(f"SmartScreen drop failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen drop error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def notify(self, message: str, display: str, priority: str) -> bool:
        # Construct the command payload for "notify"
        command = {
            "cmd": "notify",
            "msg": message,
            "duration": "30",  # set default duration; could be a parameter in the future
            "color": "blue",
            "size": "3"
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen notify failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen notify error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def toast(self, message: str, display: str, heading: str, icon: str, transition: str, duration: str) -> bool:
        # Construct the command payload for "toast"
        command = {
            "cmd": "toast",
            "msg": message,
            "heading": heading,
            "icon": icon,
            "transition": transition,
            "duration": duration
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen toast failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen toast error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def marquee(self, message: str, display: str, duration: str, color: str, size: str, bgcolor: str) -> bool:
        # Construct the command payload for "marquee"
        command = {
            "cmd": "marquee",
            "msg": message,
            "duration": duration,
            "color": color,
            "size": size,
            "bgcolor": bgcolor
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen marquee failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen marquee error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def text(self, message: str, display: str, duration: str, color: str, size: str, 
                   bgcolor: str, align: str, frame: str, animate: str, aniduration: str) -> bool:
        # Construct the command payload for "text"
        command = {
            "cmd": "text",
            "msg": message,
            "duration": duration,
            "color": color,
            "size": size,
            "bgcolor": bgcolor,
            "align": align,
            "frame": frame,
            "animate": animate,
            "aniduration": aniduration
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen text failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen text error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def app(self, url: str, display: str, duration: str, frame: str) -> bool:
        # Construct the command payload for "app"
        command = {
            "cmd": "app",
            "url": url,
            "duration": duration,
            "frame": frame
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen app failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen app error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def touch(self, option: str, display: str, value: str) -> bool:
        # Construct the command payload for "touch"
        command = {
            "cmd": "touch",
            "option": option,
            "value": value
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen touch failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen touch error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def status(self, option: str, display: str, value: str) -> bool:
        # Construct the command payload for "status"
        command = {
            "cmd": "status",
            "option": option,
            "value": value
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen status failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen status error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

    async def dj(self, option: str, display: str, value: str) -> bool:
        # Construct the command payload for "dj"
        command = {
            "cmd": "dj",
            "option": option,
            "value": value
        }
        payload = {
            "to": {"name": display},
            "data": command
        }
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"SmartScreen dj failed: {response.text}")
                return False
            result = response.json()
            if result.get("ErrCode", -1) != 0:
                print(f"SmartScreen dj error: {result.get('ErrMsg', 'Unknown error')}")
                return False
        return True

# Create an instance of our SmartScreen client.
smartscreen_client = SmartScreenClient()

@app.head("/mcp")
async def mcp_head():
    return Response(status_code=200)

@app.get("/search-youtube", summary="Search YouTube Video", response_description="URL of the most relevant YouTube video")
async def get_youtube_video_link(
    query: str = Query(..., description="The search query for YouTube.")
):
    """
    Accepts a search query and returns the YouTube link 
    for the most relevant video found.
    """
    if not YOUTUBE_API_KEY:
         raise HTTPException(status_code=500, detail="API key configuration error. Please check server logs.")

    video_id = await search_youtube_video(query)

    if video_id:
        # Construct the standard YouTube URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return {"video_url": video_url}
    else:
        # Handles cases where search failed or no results were found
        raise HTTPException(status_code=404, detail=f"No relevant YouTube video found for query: '{query}'")

@app.get("/test", tags=["test"])
async def test_endpoint():
    """
    Test endpoint to check if the API is running.
    """
    return {"message": "My name is MCP Vincent, and I am here to help you."}

# API endpoint for drop command
@app.post("/drop")
async def drop_item(request: DropRequest):
    """
    Drop an item onto the SmartScreen at the specified coordinates.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'drop' tool.
    What it does:
Displays an image or video on the screen.
Why/When to use:
Use it whenever you want to show media content—like a video, slideshow, or static image—on a particular screen area.
Key options:
• type: "url" (URLs for images/videos)
• src: one or more URLs of the media files
• duration: how long to display/play (0 = play to end)
• frame: on which screen area (e.g., main, t1, t2)
• animate: animation style (fade, slide, etc.)
• pmode: playback mode (“loop” or “random”)
    """
    success = await smartscreen_client.drop(item=request.item,x=request.x,y=request.y,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to drop item")
    return {"message": "Item dropped successfully", "item": request.item, "x": request.x, "y": request.y}

# API endpoint for notify command
@app.post("/notify")
async def notify_user(request: NotifyRequest):
    """
    Send a notification message to the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'notify' tool.
    What it does:
Shows a notification banner containing simple text.
Why/When to use:
If you want to display a short message or alert without interrupting the main screen content.
Key options:
• msg: notification text
• duration: how long to display
• color, size: appearance settings for text
    """
    success = await smartscreen_client.notify(message=request.message,priority=request.priority,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")
    return {"message": "Notification sent successfully", "notification": request.message}

# New API endpoints for additional SmartScreen commands
@app.post("/toast")
async def toast_message(request: ToastRequest):
    """
    Display a toast message on the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'toast' tool.
    What it does:
Shows a popup message with optional heading, icon, and transition effects.
Why/When to use:
Ideal for quick, transient notes (toasts) that appear and then disappear without disturbing the main content.
Key options:
• msg: main text content
• heading: optional title/heading
• icon: can be info, warning, error, or success
• transition: how it appears (plain, fade, slide)
• duration: how long the toast stays visible
    """
    success = await smartscreen_client.toast(message=request.message,heading=request.heading, 
                                          icon=request.icon,transition=request.transition,duration=request.duration,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to show toast message")
    return {"message": "Toast displayed successfully", "toast": request.message}

@app.post("/marquee")
async def marquee_text(request: MarqueeRequest):
    """
    Display scrolling marquee text on the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'marquee' tool.
    What it does:
Displays scrolling text across the screen.
Why/When to use:
Useful for announcements or continuously running messages (e.g., news ticker, short updates) in a marquee format.
Key options:
• msg: marquee text
• duration: how long to keep scrolling
• color, size: text styling
• bgcolor: background color
    """
    success = await smartscreen_client.marquee(message=request.message,duration=request.duration, 
                                           color=request.color,size=request.size,bgcolor=request.bgcolor,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to show marquee text")
    return {"message": "Marquee displayed successfully", "marquee": request.message}

@app.post("/text")
async def display_text(request: TextRequest):
    """
    Display text on the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'text' tool.
    What it does:
Shows a static block of text with customizable appearance and alignment.
Why/When to use:
Use to render text that remains on the screen for a set duration, possibly in a specific frame or layout region.
Key options:
• msg: text to display
• duration: display length (seconds)
• color, size, bgcolor: styling
• align: left, center, or right
• animate: how text appears (fade, slide, etc.)
    """
    success = await smartscreen_client.text(message=request.message,duration=request.duration, 
                                        color=request.color,size=request.size,bgcolor=request.bgcolor,
                                        align=request.align,frame=request.frame,animate=request.animate,
                                        aniduration=request.aniduration,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to show text")
    return {"message": "Text displayed successfully", "text": request.message}

@app.post("/app")
async def launch_app(request: AppRequest):
    """
    Launch a web application on the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'app' tool.
    What it does:
Loads and displays a webpage within a specified frame.
Why/When to use:
If you need to embed a browser view or show dynamic web content on the SmartScreen.
Key options:
• url: the webpage’s URL
• duration: how long to display (0 = indefinite)
• frame: target screen region
    """
    success = await smartscreen_client.app(url=request.url,duration=request.duration,frame=request.frame,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to launch app")
    return {"message": "App launched successfully", "url": request.url}

@app.post("/touch")
async def touch_command(request: TouchRequest):
    """
    Send a touch command to control the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'touch' tool.
    What it does:
Sends control commands like play/pause, next/previous, volume up/down, or console commands.
Why/When to use:
Ideal for interactive control of media playback or SmartScreen settings without reloading the main content.
Key options:
• option: specifies the control action (playnext, mute, console, etc.)
• value: additional parameter if needed (e.g., console sub-command)
    """
    success = await smartscreen_client.touch(option=request.option,value=request.value,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to execute touch command")
    return {"message": "Touch command executed successfully", "option": request.option, "value": request.value}

@app.post("/status")
async def status_command(request: StatusRequest):
    """
    Get or set status information on the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'status' tool.
    What it does:
Requests status information from the SmartScreen, such as version, frame usage, or device info.
Why/When to use:
If you need to check what’s currently playing, or retrieve system details (e.g., debugging, system health checks).
Key options:
• option: type of status (frame, ver, devinfo)
• value: additional context (like which frame)
    """
    success = await smartscreen_client.status(option=request.option,value=request.value,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to execute status command")
    return {"message": "Status command executed successfully", "option": request.option, "value": request.value}

@app.post("/dj")
async def dj_command(request: DjRequest):
    """
    Execute a DJ command on the SmartScreen.
    MCP Tool Exposure: This endpoint is exposed via MCP as the 'dj' tool.
    What it does:
Manages higher-level features like scheduling commands, changing startup behavior, toggling kiosk mode, or updating the logo.
Why/When to use:
When you want to schedule commands (to run at startup or a specific time), change the logo, or restart the SmartScreen service.
Key options:
• logo: sets a new logo URL
• kiosk: toggles kiosk mode on/off
• startcmd/schcmd: schedule commands for startup or specific time triggers
• restart: restarts the SmartScreen.
    """
    success = await smartscreen_client.dj(option=request.option, value=request.value,display=request.display)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to execute DJ command")
    return {"message": "DJ command executed successfully", "option": request.option, "value": request.value}

mcp = FastApiMCP(
    app,
    name="ultra-mcp-ss"
)
mcp.mount()  # mounts at '/mcp' by default


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
