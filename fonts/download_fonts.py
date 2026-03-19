"""
Font Downloader Script
Downloads 100+ popular fonts for the video editor
Run this script to download all fonts automatically
"""

import os
import requests
from pathlib import Path

# Create fonts directory
fonts_dir = Path('fonts')
fonts_dir.mkdir(exist_ok=True)

# Font URLs from Google Fonts
FONTS = {
    # Sans Serif Fonts
    'Roboto-Regular.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf',
    'Roboto-Bold.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf',
    'Roboto-Italic.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Italic.ttf',
    'Roboto-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-BoldItalic.ttf',
    'Roboto-Light.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Light.ttf',
    'Roboto-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-LightItalic.ttf',
    'Roboto-Medium.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Medium.ttf',
    'Roboto-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-MediumItalic.ttf',
    'Roboto-Thin.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Thin.ttf',
    'Roboto-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-ThinItalic.ttf',
    
    'OpenSans-Regular.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Regular.ttf',
    'OpenSans-Bold.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Bold.ttf',
    'OpenSans-Italic.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Italic.ttf',
    'OpenSans-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-BoldItalic.ttf',
    'OpenSans-Light.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-Light.ttf',
    'OpenSans-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-LightItalic.ttf',
    'OpenSans-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-SemiBold.ttf',
    'OpenSans-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-SemiBoldItalic.ttf',
    'OpenSans-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-ExtraBold.ttf',
    'OpenSans-ExtraBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/static/OpenSans-ExtraBoldItalic.ttf',
    
    'Poppins-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf',
    'Poppins-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf',
    'Poppins-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Italic.ttf',
    'Poppins-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-BoldItalic.ttf',
    'Poppins-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Light.ttf',
    'Poppins-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-LightItalic.ttf',
    'Poppins-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf',
    'Poppins-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-MediumItalic.ttf',
    'Poppins-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf',
    'Poppins-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBoldItalic.ttf',
    'Poppins-Thin.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Thin.ttf',
    'Poppins-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ThinItalic.ttf',
    'Poppins-ExtraLight.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraLight.ttf',
    'Poppins-ExtraLightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraLightItalic.ttf',
    'Poppins-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf',
    'Poppins-ExtraBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBoldItalic.ttf',
    'Poppins-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Black.ttf',
    'Poppins-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-BlackItalic.ttf',
    
    'Montserrat-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Regular.ttf',
    'Montserrat-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf',
    'Montserrat-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Italic.ttf',
    'Montserrat-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-BoldItalic.ttf',
    'Montserrat-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Light.ttf',
    'Montserrat-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-LightItalic.ttf',
    'Montserrat-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Medium.ttf',
    'Montserrat-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-MediumItalic.ttf',
    'Montserrat-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-SemiBold.ttf',
    'Montserrat-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-SemiBoldItalic.ttf',
    'Montserrat-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-ExtraBold.ttf',
    'Montserrat-ExtraBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-ExtraBoldItalic.ttf',
    'Montserrat-Thin.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Thin.ttf',
    'Montserrat-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-ThinItalic.ttf',
    
    'Lato-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf',
    'Lato-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf',
    'Lato-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Italic.ttf',
    'Lato-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-BoldItalic.ttf',
    'Lato-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Light.ttf',
    'Lato-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-LightItalic.ttf',
    'Lato-Thin.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Thin.ttf',
    'Lato-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-ThinItalic.ttf',
    'Lato-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Black.ttf',
    'Lato-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-BlackItalic.ttf',
    
    'Raleway-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Regular.ttf',
    'Raleway-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Bold.ttf',
    'Raleway-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Italic.ttf',
    'Raleway-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-BoldItalic.ttf',
    'Raleway-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Light.ttf',
    'Raleway-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-LightItalic.ttf',
    'Raleway-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Medium.ttf',
    'Raleway-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-MediumItalic.ttf',
    'Raleway-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-SemiBold.ttf',
    'Raleway-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-SemiBoldItalic.ttf',
    'Raleway-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-ExtraBold.ttf',
    'Raleway-ExtraBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-ExtraBoldItalic.ttf',
    'Raleway-Thin.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Thin.ttf',
    'Raleway-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-ThinItalic.ttf',
    'Raleway-ExtraLight.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-ExtraLight.ttf',
    'Raleway-ExtraLightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-ExtraLightItalic.ttf',
    'Raleway-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Black.ttf',
    'Raleway-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-BlackItalic.ttf',
    
    'Ubuntu-Regular.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Regular.ttf',
    'Ubuntu-Bold.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Bold.ttf',
    'Ubuntu-Italic.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Italic.ttf',
    'Ubuntu-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-BoldItalic.ttf',
    'Ubuntu-Light.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Light.ttf',
    'Ubuntu-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-LightItalic.ttf',
    'Ubuntu-Medium.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Medium.ttf',
    'Ubuntu-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-MediumItalic.ttf',
    
    'Oswald-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-Regular.ttf',
    'Oswald-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-Bold.ttf',
    'Oswald-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-Light.ttf',
    'Oswald-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-Medium.ttf',
    'Oswald-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-SemiBold.ttf',
    'Oswald-ExtraLight.ttf': 'https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-ExtraLight.ttf',
    
    'Nunito-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Regular.ttf',
    'Nunito-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Bold.ttf',
    'Nunito-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Italic.ttf',
    'Nunito-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-BoldItalic.ttf',
    'Nunito-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Light.ttf',
    'Nunito-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-LightItalic.ttf',
    'Nunito-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Medium.ttf',
    'Nunito-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-MediumItalic.ttf',
    'Nunito-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-SemiBold.ttf',
    'Nunito-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-SemiBoldItalic.ttf',
    'Nunito-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-ExtraBold.ttf',
    'Nunito-ExtraBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-ExtraBoldItalic.ttf',
    'Nunito-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Black.ttf',
    'Nunito-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-BlackItalic.ttf',
    
    'Quicksand-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/quicksand/static/Quicksand-Regular.ttf',
    'Quicksand-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/quicksand/static/Quicksand-Bold.ttf',
    'Quicksand-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/quicksand/static/Quicksand-Light.ttf',
    'Quicksand-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/quicksand/static/Quicksand-Medium.ttf',
    'Quicksand-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/quicksand/static/Quicksand-SemiBold.ttf',
    
    'JosefinSans-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-Regular.ttf',
    'JosefinSans-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-Bold.ttf',
    'JosefinSans-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-Italic.ttf',
    'JosefinSans-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-BoldItalic.ttf',
    'JosefinSans-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-Light.ttf',
    'JosefinSans-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-LightItalic.ttf',
    'JosefinSans-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-Medium.ttf',
    'JosefinSans-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-MediumItalic.ttf',
    'JosefinSans-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-SemiBold.ttf',
    'JosefinSans-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-SemiBoldItalic.ttf',
    'JosefinSans-Thin.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-Thin.ttf',
    'JosefinSans-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/josefinsans/static/JosefinSans-ThinItalic.ttf',
    
    # Serif Fonts
    'Merriweather-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Regular.ttf',
    'Merriweather-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Bold.ttf',
    'Merriweather-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Italic.ttf',
    'Merriweather-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-BoldItalic.ttf',
    'Merriweather-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Light.ttf',
    'Merriweather-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-LightItalic.ttf',
    'Merriweather-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Black.ttf',
    'Merriweather-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-BlackItalic.ttf',
    
    'PlayfairDisplay-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Regular.ttf',
    'PlayfairDisplay-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf',
    'PlayfairDisplay-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Italic.ttf',
    'PlayfairDisplay-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-BoldItalic.ttf',
    'PlayfairDisplay-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Black.ttf',
    'PlayfairDisplay-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-BlackItalic.ttf',
    'PlayfairDisplay-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Medium.ttf',
    'PlayfairDisplay-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-MediumItalic.ttf',
    'PlayfairDisplay-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-SemiBold.ttf',
    'PlayfairDisplay-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-SemiBoldItalic.ttf',
    'PlayfairDisplay-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-ExtraBold.ttf',
    'PlayfairDisplay-ExtraBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-ExtraBoldItalic.ttf',
    
    'Lora-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Regular.ttf',
    'Lora-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Bold.ttf',
    'Lora-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Italic.ttf',
    'Lora-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-BoldItalic.ttf',
    'Lora-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Medium.ttf',
    'Lora-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-MediumItalic.ttf',
    'Lora-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-SemiBold.ttf',
    'Lora-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-SemiBoldItalic.ttf',
    
    'CormorantGaramond-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Regular.ttf',
    'CormorantGaramond-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Bold.ttf',
    'CormorantGaramond-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Italic.ttf',
    'CormorantGaramond-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-BoldItalic.ttf',
    'CormorantGaramond-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Light.ttf',
    'CormorantGaramond-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-LightItalic.ttf',
    'CormorantGaramond-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Medium.ttf',
    'CormorantGaramond-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-MediumItalic.ttf',
    'CormorantGaramond-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-SemiBold.ttf',
    'CormorantGaramond-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-SemiBoldItalic.ttf',
    
    'CrimsonText-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-Regular.ttf',
    'CrimsonText-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-Bold.ttf',
    'CrimsonText-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-Italic.ttf',
    'CrimsonText-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-BoldItalic.ttf',
    'CrimsonText-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-SemiBold.ttf',
    'CrimsonText-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-SemiBoldItalic.ttf',
    'CrimsonText-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-Medium.ttf',
    'CrimsonText-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-MediumItalic.ttf',
    
    # Handwriting Fonts
    'DancingScript-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/dancingscript/static/DancingScript-Regular.ttf',
    'DancingScript-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/dancingscript/static/DancingScript-Bold.ttf',
    'DancingScript-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/dancingscript/static/DancingScript-Medium.ttf',
    'DancingScript-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/dancingscript/static/DancingScript-SemiBold.ttf',
    
    'Pacifico-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf',
    
    'Lobster-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/lobster/Lobster-Regular.ttf',
    'LobsterTwo-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/lobstertwo/LobsterTwo-Regular.ttf',
    'LobsterTwo-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/lobstertwo/LobsterTwo-Bold.ttf',
    'LobsterTwo-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lobstertwo/LobsterTwo-Italic.ttf',
    'LobsterTwo-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lobstertwo/LobsterTwo-BoldItalic.ttf',
    
    'ShadowsIntoLight-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/shadowsintolight/ShadowsIntoLight.ttf',
    'ShadowsIntoLightTwo-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/shadowsintolighttwo/ShadowsIntoLightTwo-Regular.ttf',
    
    'IndieFlower-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower.ttf',
    
    'Caveat-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Regular.ttf',
    'Caveat-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Bold.ttf',
    'Caveat-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Medium.ttf',
    'Caveat-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-SemiBold.ttf',
    
    'Courgette-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/courgette/Courgette-Regular.ttf',
    
    'Kalam-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf',
    'Kalam-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Bold.ttf',
    'Kalam-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Light.ttf',
    
    'GreatVibes-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf',
    
    'AlexBrush-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/alexbrush/AlexBrush-Regular.ttf',
    
    'Allura-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/allura/Allura-Regular.ttf',
    
    'AmaticSC-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/amaticsc/AmaticSC-Regular.ttf',
    'AmaticSC-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/amaticsc/AmaticSC-Bold.ttf',
    
    'BadScript-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/badscript/BadScript-Regular.ttf',
    
    'BerkshireSwash-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/berkshireswash/BerkshireSwash-Regular.ttf',
    
    'Cookie-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/cookie/Cookie-Regular.ttf',
    
    'GrandHotel-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/grandhotel/GrandHotel-Regular.ttf',
    
    'Handlee-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/handlee/Handlee-Regular.ttf',
    
    'Italianno-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/italianno/Italianno-Regular.ttf',
    
    'KristenITC-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/kristenitc/KristenITC-Regular.ttf',
    
    'Meddon-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/meddon/Meddon-Regular.ttf',
    
    'Merienda-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/merienda/static/Merienda-Regular.ttf',
    'Merienda-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/merienda/static/Merienda-Bold.ttf',
    
    'Miniver-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/miniver/Miniver-Regular.ttf',
    
    'MrDafoe-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/mrdafoe/MrDafoe-Regular.ttf',
    
    'MrsSaintDelafield-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/mrssaintdelafield/MrsSaintDelafield-Regular.ttf',
    
    'Norican-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/norican/Norican-Regular.ttf',
    
    'Parisienne-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/parisienne/Parisienne-Regular.ttf',
    
    'PinyonScript-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/pinyonscript/PinyonScript-Regular.ttf',
    
    'Sacramento-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/sacramento/Sacramento-Regular.ttf',
    
    'Satisfy-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/satisfy/Satisfy-Regular.ttf',
    
    'Tangerine-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/tangerine/Tangerine-Regular.ttf',
    'Tangerine-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/tangerine/Tangerine-Bold.ttf',
    
    # Monospace Fonts
    'SourceCodePro-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-Regular.ttf',
    'SourceCodePro-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-Bold.ttf',
    'SourceCodePro-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-Italic.ttf',
    'SourceCodePro-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-BoldItalic.ttf',
    'SourceCodePro-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-Light.ttf',
    'SourceCodePro-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-LightItalic.ttf',
    'SourceCodePro-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-Medium.ttf',
    'SourceCodePro-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-MediumItalic.ttf',
    'SourceCodePro-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-SemiBold.ttf',
    'SourceCodePro-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-SemiBoldItalic.ttf',
    'SourceCodePro-ExtraLight.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-ExtraLight.ttf',
    'SourceCodePro-ExtraLightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-ExtraLightItalic.ttf',
    'SourceCodePro-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-Black.ttf',
    'SourceCodePro-BlackItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/sourcecodepro/static/SourceCodePro-BlackItalic.ttf',
    
    'CourierPrime-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Regular.ttf',
    'CourierPrime-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Bold.ttf',
    'CourierPrime-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Italic.ttf',
    'CourierPrime-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-BoldItalic.ttf',
    
    'Inconsolata-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-Regular.ttf',
    'Inconsolata-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-Bold.ttf',
    'Inconsolata-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-Light.ttf',
    'Inconsolata-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-Medium.ttf',
    'Inconsolata-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-SemiBold.ttf',
    'Inconsolata-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-ExtraBold.ttf',
    'Inconsolata-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/inconsolata/static/Inconsolata-Black.ttf',
    
    'SpaceMono-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Regular.ttf',
    'SpaceMono-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Bold.ttf',
    'SpaceMono-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Italic.ttf',
    'SpaceMono-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-BoldItalic.ttf',
    
    # Display Fonts
    'Bangers-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf',
    
    'Anton-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf',
    
    'ArchitectsDaughter-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf',
    
    'BebasNeue-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf',
    
    'Comfortaa-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/comfortaa/static/Comfortaa-Regular.ttf',
    'Comfortaa-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/comfortaa/static/Comfortaa-Bold.ttf',
    'Comfortaa-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/comfortaa/static/Comfortaa-Light.ttf',
    'Comfortaa-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/comfortaa/static/Comfortaa-Medium.ttf',
    'Comfortaa-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/comfortaa/static/Comfortaa-SemiBold.ttf',
    
    'FredokaOne-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/fredokaone/FredokaOne-Regular.ttf',
    
    'Jost-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-Regular.ttf',
    'Jost-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-Bold.ttf',
    'Jost-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-Italic.ttf',
    'Jost-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-BoldItalic.ttf',
    'Jost-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-Light.ttf',
    'Jost-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-LightItalic.ttf',
    'Jost-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-Medium.ttf',
    'Jost-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-MediumItalic.ttf',
    'Jost-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-SemiBold.ttf',
    'Jost-SemiBoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-SemiBoldItalic.ttf',
    'Jost-Thin.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-Thin.ttf',
    'Jost-ThinItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-ThinItalic.ttf',
    'Jost-ExtraLight.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-ExtraLight.ttf',
    'Jost-ExtraLightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/jost/static/Jost-ExtraLightItalic.ttf',
    
    'LilitaOne-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/lilitaone/LilitaOne-Regular.ttf',
    
    'LuckiestGuy-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/luckiestguy/LuckiestGuy-Regular.ttf',
    
    'Orbitron-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-Regular.ttf',
    'Orbitron-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-Bold.ttf',
    'Orbitron-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-Black.ttf',
    'Orbitron-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-Medium.ttf',
    'Orbitron-SemiBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-SemiBold.ttf',
    'Orbitron-ExtraBold.ttf': 'https://github.com/google/fonts/raw/main/ofl/orbitron/static/Orbitron-ExtraBold.ttf',
    
    'PassionOne-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/passionone/PassionOne-Regular.ttf',
    'PassionOne-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/passionone/PassionOne-Bold.ttf',
    'PassionOne-Black.ttf': 'https://github.com/google/fonts/raw/main/ofl/passionone/PassionOne-Black.ttf',
    
    'PressStart2P-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf',
    
    'Righteous-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/righteous/Righteous-Regular.ttf',
    
    'Rubik-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-Regular.ttf',
    'Rubik-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-Bold.ttf',
    'Rubik-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-Italic.ttf',
    'Rubik-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-BoldItalic.ttf',
    'Rubik-Light.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-Light.ttf',
    'Rubik-LightItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-LightItalic.ttf',
    'Rubik-Medium.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-Medium.ttf',
    'Rubik-MediumItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/rubik/static/Rubik-MediumItalic.ttf',
    
    'SigmarOne-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/sigmarone/SigmarOne-Regular.ttf',
    
    'TitanOne-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/titanone/TitanOne-Regular.ttf',
    
    'ZCOOLKuaiLe-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf',
}

def download_fonts():
    """Download all fonts"""
    print("🎨 Downloading 100+ fonts for Video Editor Bot...")
    print("=" * 50)
    
    total = len(FONTS)
    success = 0
    failed = 0
    
    for i, (font_name, url) in enumerate(FONTS.items(), 1):
        font_path = fonts_dir / font_name
        
        # Skip if already exists
        if font_path.exists():
            print(f"✓ [{i}/{total}] {font_name} already exists")
            success += 1
            continue
        
        try:
            print(f"↓ [{i}/{total}] Downloading {font_name}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            with open(font_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ [{i}/{total}] {font_name} downloaded successfully")
            success += 1
            
        except Exception as e:
            print(f"✗ [{i}/{total}] Failed to download {font_name}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"✅ Download complete! {success} fonts downloaded, {failed} failed")
    
    # Create font list file
    create_font_list()
    
    return success, failed

def create_font_list():
    """Create a JSON file with font information"""
    font_list = []
    
    for font_file in fonts_dir.glob("*.ttf"):
        name = font_file.stem.replace('-', ' ').replace('_', ' ')
        font_list.append({
            'file': font_file.name,
            'name': name,
            'path': str(font_file)
        })
    
    # Sort by name
    font_list.sort(key=lambda x: x['name'])
    
    # Save to JSON
    with open(fonts_dir / 'fonts.json', 'w') as f:
        json.dump(font_list, f, indent=2)
    
    print(f"📝 Created fonts.json with {len(font_list)} fonts")

if __name__ == "__main__":
    download_fonts()
