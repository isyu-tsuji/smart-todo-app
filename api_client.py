"""
外部API通信モジュール
OpenWeatherMap API連携
"""
import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from config import Config


class WeatherAPIError(Exception):
    """天気API関連のエラー"""
    pass


def get_weather(location: str) -> Optional[Dict[str, Any]]:
    """
    OpenWeatherMap APIから天気情報を取得します。
    
    Args:
        location: 都市名（例: "Tokyo", "Osaka"）
    
    Returns:
        天気情報を含む辞書、またはNone（エラー時）
        形式:
        {
            "temp": 15.5,
            "condition": "晴れ",
            "description": "clear sky",
            "icon": "01d",
            "is_bad_weather": False  # 雨や雪の場合True
        }
    
    Raises:
        WeatherAPIError: API呼び出しに失敗した場合
    """
    if not location:
        return None
    
    api_key = Config.OPENWEATHER_API_KEY
    if not api_key:
        # APIキーが設定されていない場合はNoneを返す（エラーにはしない）
        return None
    
    try:
        # APIパラメータ
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric',  # 摂氏
            'lang': 'ja'        # 日本語
        }
        
        # API呼び出し
        response = requests.get(
            Config.OPENWEATHER_API_URL,
            params=params,
            timeout=5  # 5秒のタイムアウト
        )
        
        # HTTPエラーチェック
        response.raise_for_status()
        
        # JSONレスポンスをパース
        data = response.json()
        
        # 天気情報を抽出
        weather_main = data.get('weather', [{}])[0].get('main', '')
        weather_description = data.get('weather', [{}])[0].get('description', '')
        weather_icon = data.get('weather', [{}])[0].get('icon', '')
        temp = data.get('main', {}).get('temp')
        
        # 悪天候の判定（雨、雪、嵐など）
        bad_weather_conditions = ['Rain', 'Snow', 'Thunderstorm', 'Drizzle']
        is_bad_weather = weather_main in bad_weather_conditions
        
        return {
            'temp': round(temp, 1) if temp is not None else None,
            'condition': weather_description or weather_main,
            'description': weather_description,
            'icon': weather_icon,
            'is_bad_weather': is_bad_weather,
            'location': data.get('name', location)
        }
        
    except requests.exceptions.Timeout:
        # タイムアウトエラー
        raise WeatherAPIError(f"Weather API request timeout for location: {location}")
    except requests.exceptions.RequestException as e:
        # その他のリクエストエラー
        raise WeatherAPIError(f"Weather API request failed for location: {location}: {str(e)}")
    except (KeyError, ValueError, IndexError) as e:
        # JSONパースエラーや予期しないレスポンス形式
        raise WeatherAPIError(f"Failed to parse weather API response for location: {location}: {str(e)}")
    except Exception as e:
        # その他の予期しないエラー
        raise WeatherAPIError(f"Unexpected error while fetching weather for location: {location}: {str(e)}")


def get_weather_safe(location: str) -> Optional[Dict[str, Any]]:
    """
    天気情報を取得します（エラー時はNoneを返す安全版）。
    
    Args:
        location: 都市名
    
    Returns:
        天気情報を含む辞書、またはNone（エラー時）
    """
    try:
        return get_weather(location)
    except WeatherAPIError:
        # エラーはログに記録するが、アプリケーションは継続
        # 本番環境ではロガーを使用することを推奨
        return None


