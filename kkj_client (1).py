# -*- coding: utf-8 -*-
"""
官公需情報ポータルサイト検索API (http://www.kkj.go.jp/api/) の
呼び出し・パース処理をまとめた共通モジュール。
app.py (Webアプリ) と notify.py (新着メール通知バッチ) の両方から使う。
"""

from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET

import requests

KKJ_API_URL = "http://www.kkj.go.jp/api/"

# 都道府県コード(JIS X0401)
PREFECTURES = [
    ("01", "北海道"), ("02", "青森県"), ("03", "岩手県"), ("04", "宮城県"),
    ("05", "秋田県"), ("06", "山形県"), ("07", "福島県"), ("08", "茨城県"),
    ("09", "栃木県"), ("10", "群馬県"), ("11", "埼玉県"), ("12", "千葉県"),
    ("13", "東京都"), ("14", "神奈川県"), ("15", "新潟県"), ("16", "富山県"),
    ("17", "石川県"), ("18", "福井県"), ("19", "山梨県"), ("20", "長野県"),
    ("21", "岐阜県"), ("22", "静岡県"), ("23", "愛知県"), ("24", "三重県"),
    ("25", "滋賀県"), ("26", "京都府"), ("27", "大阪府"), ("28", "兵庫県"),
    ("29", "奈良県"), ("30", "和歌山県"), ("31", "鳥取県"), ("32", "島根県"),
    ("33", "岡山県"), ("34", "広島県"), ("35", "山口県"), ("36", "徳島県"),
    ("37", "香川県"), ("38", "愛媛県"), ("39", "高知県"), ("40", "福岡県"),
    ("41", "佐賀県"), ("42", "長崎県"), ("43", "熊本県"), ("44", "大分県"),
    ("45", "宮崎県"), ("46", "鹿児島県"), ("47", "沖縄県"),
]

CATEGORIES = [("1", "物品"), ("2", "工事"), ("3", "役務")]
CATEGORY_LABEL = dict(CATEGORIES)

PROCEDURE_TYPES = [
    ("1", "一般競争入札"),
    ("2", "簡易公募型競争入札"),
    ("3", "簡易公募型指名競争入札"),
]
PROCEDURE_TYPE_LABEL = dict(PROCEDURE_TYPES)

CERTIFICATIONS = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]

# 信号機関連として検索するキーワード群(OR検索)
SIGNAL_KEYWORDS = [
    "信号機", "信号灯器", "信号制御機", "押ボタン信号", "押しボタン信号",
    "歩行者用灯器", "灯器", "信号柱", "交通信号",
]
SIGNAL_QUERY = " OR ".join(SIGNAL_KEYWORDS)

ORGANIZATION_NAME = "国家公安委員会"


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    return el.text.strip()


def _parse_iso_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def status_for_deadline(deadline: str | None) -> str:
    """締切までの残り日数から信号(green/yellow/red/gray)を判定する"""
    d = _parse_iso_date(deadline)
    if d is None:
        return "gray"
    days_left = (d - dt.date.today()).days
    if days_left < 0:
        return "gray"
    if days_left <= 3:
        return "red"
    if days_left <= 10:
        return "yellow"
    return "green"


def fetch_kkj(params: dict) -> ET.Element:
    resp = requests.get(KKJ_API_URL, params=params, timeout=20)
    resp.encoding = "utf-8"
    return ET.fromstring(resp.text)


def search(
    prefecture: str = "",
    category: str = "",
    procedure_type: str = "",
    certification: str = "",
    cft_issue_date: str = "",
    count: str = "1000",
) -> dict:
    """
    信号機関連・国家公安委員会の入札情報を検索する。
    戻り値: {"error": str|None, "searchHits": str, "results": [dict, ...]}
    results は締切が近い順(締切日情報がないものは最後)に並び替え済み。
    """
    params = {"Query": SIGNAL_QUERY, "Organization_Name": ORGANIZATION_NAME, "Count": count}
    if prefecture:
        params["LG_Code"] = prefecture
    if category:
        params["Category"] = category
    if procedure_type:
        params["Procedure_Type"] = procedure_type
    if certification:
        params["Certification"] = certification
    if cft_issue_date:
        params["CFT_Issue_Date"] = cft_issue_date

    try:
        root = fetch_kkj(params)
    except requests.RequestException:
        return {
            "error": "官公需情報ポータルサイトへの接続に失敗しました。時間をおいて再度お試しください。",
            "searchHits": "0",
            "results": [],
        }
    except ET.ParseError:
        return {"error": "検索結果の解析に失敗しました。", "searchHits": "0", "results": []}

    error_el = root.find("Error")
    if error_el is not None:
        return {"error": _text(error_el) or "検索でエラーが発生しました。", "searchHits": "0", "results": []}

    search_hits = _text(root.find("SearchResults/SearchHits")) or "0"

    results = []
    for node in root.findall("SearchResults/SearchResult"):
        deadline = _text(node.find("TenderSubmissionDeadline"))

        attachments = []
        for att in node.findall("Attachments/Attachment"):
            name = _text(att.find("Name"))
            uri = _text(att.find("Uri"))
            if uri:
                attachments.append({"name": name or "添付ファイル", "uri": uri})

        results.append({
            "key": _text(node.find("Key")),
            "projectName": _text(node.find("ProjectName")),
            "organizationName": _text(node.find("OrganizationName")),
            "prefectureName": _text(node.find("PrefectureName")),
            "cityName": _text(node.find("CityName")),
            "category": _text(node.find("Category")),
            "procedureType": _text(node.find("ProcedureType")),
            "certification": _text(node.find("Certification")),
            "cftIssueDate": _text(node.find("CftIssueDate")),
            "tenderSubmissionDeadline": deadline,
            "openingTendersEvent": _text(node.find("OpeningTendersEvent")),
            "periodEndTime": _text(node.find("PeriodEndTime")),
            "location": _text(node.find("Location")),
            "externalDocumentURI": _text(node.find("ExternalDocumentURI")),
            "attachments": attachments,
            "status": status_for_deadline(deadline),
        })

    # 締切が近い順に並び替え。締切日情報がないものは最後に回す。
    def sort_key(r):
        d = _parse_iso_date(r["tenderSubmissionDeadline"])
        return (d is None, d or dt.date.max)

    results.sort(key=sort_key)

    return {"error": None, "searchHits": search_hits, "results": results}
