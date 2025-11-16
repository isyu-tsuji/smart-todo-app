"""
外部API通信モジュール
OpenWeatherMap API連携
"""
import logging
import re
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import Config

# ロガー設定
logger = logging.getLogger(__name__)

# セッション管理（接続の再利用）
_session: Optional[requests.Session] = None


class WeatherAPIError(Exception):
    """天気API関連のエラー"""
    pass


def _get_session() -> requests.Session:
    """
    HTTPセッションを取得します（接続の再利用）。
    
    Returns:
        requests.Session: 設定済みのセッションオブジェクト
    """
    global _session
    if _session is None:
        _session = requests.Session()
        
        # リトライ戦略の設定
        retry_strategy = Retry(
            total=3,  # 最大3回リトライ
            backoff_factor=1,  # リトライ間隔: 1秒, 2秒, 4秒
            status_forcelist=[429, 500, 502, 503, 504],  # リトライするHTTPステータスコード
            allowed_methods=["GET"]  # GETリクエストのみリトライ
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    
    return _session


def _validate_location(location: str) -> bool:
    """
    ロケーション文字列を検証します。
    
    Args:
        location: 検証するロケーション文字列
    
    Returns:
        bool: 有効な場合はTrue
    """
    if not location or not isinstance(location, str):
        return False
    
    # 長さ制限（OpenWeatherMap APIの制限を考慮）
    if len(location) > 100:
        return False
    
    # 危険な文字をチェック（基本的なサニタイゼーション）
    # 都市名に含まれる可能性のある文字（スペース、ハイフン、アポストロフィなど）は許可
    dangerous_patterns = re.compile(r'[<>"\'\\]')
    if dangerous_patterns.search(location):
        return False
    
    return True


def _handle_http_error(response: requests.Response, location: str) -> None:
    """
    HTTPエラーレスポンスを処理します。
    
    Args:
        response: HTTPレスポンスオブジェクト
        location: リクエストしたロケーション
    
    Raises:
        WeatherAPIError: 適切なエラーメッセージと共に
    """
    status_code = response.status_code
    
    if status_code == 401:
        logger.error(f"OpenWeatherMap API認証エラー: APIキーが無効です (location: {location})")
        raise WeatherAPIError("API認証に失敗しました。APIキーを確認してください。")
    elif status_code == 403:
        logger.error(f"OpenWeatherMap API権限エラー: アクセスが拒否されました (location: {location})")
        raise WeatherAPIError("APIへのアクセスが拒否されました。")
    elif status_code == 404:
        logger.warning(f"OpenWeatherMap API: ロケーションが見つかりません (location: {location})")
        raise WeatherAPIError(f"ロケーション '{location}' が見つかりませんでした。")
    elif status_code == 429:
        logger.warning(f"OpenWeatherMap API: レート制限に達しました (location: {location})")
        raise WeatherAPIError("APIのレート制限に達しました。しばらく待ってから再試行してください。")
    elif status_code >= 500:
        logger.error(f"OpenWeatherMap APIサーバーエラー: {status_code} (location: {location})")
        raise WeatherAPIError(f"APIサーバーエラーが発生しました (ステータスコード: {status_code})")
    else:
        logger.error(f"OpenWeatherMap API: 予期しないHTTPエラー {status_code} (location: {location})")
        raise WeatherAPIError(f"APIリクエストが失敗しました (ステータスコード: {status_code})")


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
    # 入力検証
    if not _validate_location(location):
        logger.warning(f"無効なロケーション文字列: {location}")
        raise WeatherAPIError(f"無効なロケーションです: {location}")
    
    api_key = Config.OPENWEATHER_API_KEY
    if not api_key:
        logger.warning("OpenWeatherMap APIキーが設定されていません")
        return None
    
    try:
        # APIパラメータ
        params = {
            'q': location.strip(),  # 前後の空白を削除
            'appid': api_key,
            'units': 'metric',  # 摂氏
            'lang': 'ja'        # 日本語
        }
        
        # セッションを取得してAPI呼び出し
        session = _get_session()
        response = session.get(
            Config.OPENWEATHER_API_URL,
            params=params,
            timeout=10  # タイムアウトを10秒に延長（リトライを考慮）
        )
        
        # HTTPエラーチェック
        if not response.ok:
            _handle_http_error(response, location)
        
        # JSONレスポンスをパース
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"OpenWeatherMap API: JSONパースエラー (location: {location}): {e}")
            raise WeatherAPIError(f"APIレスポンスの解析に失敗しました: {str(e)}")
        
        # 天気情報を抽出（安全に）
        weather_list = data.get('weather', [])
        if not weather_list or not isinstance(weather_list, list):
            logger.warning(f"OpenWeatherMap API: 天気情報が空です (location: {location})")
            weather_data = {}
        else:
            weather_data = weather_list[0] if isinstance(weather_list[0], dict) else {}
        
        weather_main = weather_data.get('main', '') or ''
        weather_description = weather_data.get('description', '') or ''
        weather_icon = weather_data.get('icon', '') or ''
        
        main_data = data.get('main', {})
        if not isinstance(main_data, dict):
            main_data = {}
        temp = main_data.get('temp')
        
        # 悪天候の判定（雨、雪、嵐など）
        bad_weather_conditions = ['Rain', 'Snow', 'Thunderstorm', 'Drizzle']
        is_bad_weather = weather_main in bad_weather_conditions
        
        result = {
            'temp': round(temp, 1) if temp is not None else None,
            'condition': weather_description or weather_main or '不明',
            'description': weather_description or '',
            'icon': weather_icon,
            'is_bad_weather': is_bad_weather,
            'location': data.get('name', location) if isinstance(data.get('name'), str) else location
        }
        
        logger.debug(f"天気情報を取得しました: {location} -> {result.get('condition')}")
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"OpenWeatherMap API: タイムアウト (location: {location})")
        raise WeatherAPIError(f"APIリクエストがタイムアウトしました: {location}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"OpenWeatherMap API: 接続エラー (location: {location}): {e}")
        raise WeatherAPIError(f"APIへの接続に失敗しました: {location}")
    except WeatherAPIError:
        # 既に処理済みのエラーはそのまま再発生
        raise
    except Exception as e:
        logger.exception(f"OpenWeatherMap API: 予期しないエラー (location: {location})")
        raise WeatherAPIError(f"予期しないエラーが発生しました: {str(e)}")


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
    except WeatherAPIError as e:
        # エラーをログに記録し、アプリケーションは継続
        logger.warning(f"天気情報の取得に失敗しました (location: {location}): {e}")
        return None


