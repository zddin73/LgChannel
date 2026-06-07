import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from xml.dom import minidom
from lg_scraper import LGChannelsScraper  # Replace with your actual filename

def generate_m3u(channels, filename="lg_playlist.m3u"):
    """Generates an M3U8/M3U playlist from channel data."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            # Build M3U metadata tags
            meta = f'#EXTINF:-1 tvg-id="{ch.source_channel_id}" tvg-name="{ch.name}"'
            if ch.logo_url:
                meta += f' tvg-logo="{ch.logo_url}"'
            if ch.category:
                meta += f' group-title="{ch.category}"'
            if ch.number:
                meta += f' tvg-chno="{ch.number}"'
            
            f.write(f"{meta},{ch.name}\n")
            f.write(f"{ch.stream_url}\n")
    print(f"[Success] Generated M3U playlist: {filename}")

def generate_xmltv(channels, programs, filename="lg.xml"):
    """Generates an XMLTV format EPG file."""
    root = ET.Element("tv")
    root.set("generator-info-name", "LG Channels Scraper")

    # 1. Append Channel Elements
    for ch in channels:
        channel_elem = ET.SubElement(root, "channel", id=ch.source_channel_id)
        
        display_name = ET.SubElement(channel_elem, "display-name")
        display_name.text = ch.name
        
        if ch.logo_url:
            logo = ET.SubElement(channel_elem, "icon", src=ch.logo_url)

    # 2. Append Program Elements
    # Format required by XMLTV: YYYYMMDDhhmmss +HHMM
    xmltv_dt_format = "%Y%m%d%H%M%S %z"

    for prog in programs:
        start_str = prog.start_time.strftime(xmltv_dt_format)
        end_str = prog.end_time.strftime(xmltv_dt_format)

        prog_elem = ET.SubElement(
            root, 
            "programme", 
            channel=prog.source_channel_id, 
            start=start_str, 
            stop=end_str
        )

        title = ET.SubElement(prog_elem, "title")
        title.text = prog.title

        if prog.description:
            desc = ET.SubElement(prog_elem, "desc")
            desc.text = prog.description

        if prog.category:
            # Handle split categories if they exist (e.g. "Movie;Drama")
            for cat in prog.category.split(";"):
                category = ET.SubElement(prog_elem, "category")
                category.text = cat

        if prog.poster_url:
            icon = ET.SubElement(prog_elem, "icon", src=prog.poster_url)

        if prog.rating:
            rating = ET.SubElement(prog_elem, "rating", system="VCHIP")
            value = ET.SubElement(rating, "value")
            value.text = prog.rating

        if prog.episode_id:
            # tms_id format for XMLTV providers
            episode_num = ET.SubElement(prog_elem, "episode-num", system="dd_progid")
            episode_num.text = prog.episode_id

    # 3. Pretty print and write to file
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ", encoding="utf-8")

    with open(filename, "wb") as f:
        f.write(pretty_xml)
    print(f"[Success] Generated XMLTV EPG: {filename}")

def main():
    # Initialize the LG scraper
    scraper = LGChannelsScraper()
    
    print("Scraping channels...")
    channels = scraper.fetch_channels()
    
    if not channels:
        print("No channels found. Exiting.")
        return

    # Process and expand stream URLs using the resolve macro helper
    for ch in channels:
        ch.stream_url = scraper.resolve(ch.stream_url)

    print("Scraping EPG programs...")
    programs = scraper.fetch_epg(channels)

    # Output to files
    generate_m3u(channels, "lg_playlist.m3u")
    generate_xmltv(channels, programs, "lg.xml")

if __name__ == "__main__":
    main()
