from unittest.mock import MagicMock, patch
from tvm_multi_scan_exporter.scan_fetcher import ScansFetcher
from tvm_multi_scan_exporter.models import Scan, ScanHistory
from tvm_multi_scan_exporter.configuration import Config
from tvm_multi_scan_exporter.constants import CURRENT_TIME


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_scan_histories_with_matching_scans_and_histories(mock_tio):
    # Mock TenableIO and Config
    mock_tio.scans.list.return_value = [
        {"uuid": "uuid1", "name": "Test Scan 1", "schedule_uuid": "sched1", "id": 1},
        {"uuid": "uuid2", "name": "Test Scan 2", "schedule_uuid": "sched2", "id": 2},
    ]
    mock_tio.scans.history.side_effect = [
        [{"id": "h1", "status": "completed", "time_end": CURRENT_TIME - 100}],
        [{"id": "h2", "status": "completed", "time_end": CURRENT_TIME - 200}],
    ]
    config = Config(scan_name="Test Scan", allowed_memory_gb=2,
                    window=MagicMock(since=CURRENT_TIME - 3600, upto=CURRENT_TIME))

    fetcher = ScansFetcher(mock_tio)
    histories = fetcher.scan_histories(config)

    assert len(histories) == 2
    assert histories[0] == ScanHistory(
        id="h1", status="completed", time_end=CURRENT_TIME - 100, schedule_uuid="sched1", schedule_id=1
    )
    assert histories[1] == ScanHistory(
        id="h2", status="completed", time_end=CURRENT_TIME - 200, schedule_uuid="sched2", schedule_id=2
    )


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_scans_by_name_filters_correctly(mock_tio):
    # Mock TenableIO
    mock_tio.scans.list.return_value = [
        {"uuid": "uuid1", "name": "Test Scan 1", "schedule_uuid": "sched1", "id": 1},
        {"uuid": "uuid2", "name": "Other Scan", "schedule_uuid": "sched2", "id": 2},
    ]
    config = Config(scan_name="Test Scan", allowed_memory_gb=2)

    fetcher = ScansFetcher(mock_tio)
    scans = fetcher._scans_by_name(config)

    assert len(scans) == 1
    assert scans[0] == Scan(uuid="uuid1", name="Test Scan 1", schedule_uuid="sched1", id=1)


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_histories_for_scan_filters_correctly(mock_tio):
    # Mock TenableIO
    mock_tio.scans.history.return_value = [
        {"id": "h1", "status": "completed", "time_end": CURRENT_TIME - 100},
        {"id": "h2", "status": "running", "time_end": CURRENT_TIME - 200},
    ]
    config = Config(scan_name="Test Scan", allowed_memory_gb=2,
                    window=MagicMock(since=CURRENT_TIME - 3600, upto=CURRENT_TIME))

    scan = Scan(uuid="uuid1", name="Test Scan", schedule_uuid="sched1", id=1)
    fetcher = ScansFetcher(mock_tio)
    histories = fetcher._histories_for_scan(scan, config)

    assert len(histories) == 1
    assert histories[0] == ScanHistory(
        id="h1", status="completed", time_end=CURRENT_TIME - 100, schedule_uuid="sched1", schedule_id=1
    )


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_scan_histories_with_no_matching_scans(mock_tio):
    # Mock TenableIO
    mock_tio.scans.list.return_value = []
    config = Config(scan_name="Nonexistent Scan", allowed_memory_gb=2)

    fetcher = ScansFetcher(mock_tio)
    histories = fetcher.scan_histories(config)

    assert len(histories) == 0


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_histories_with_no_matching_histories(mock_tio):
    # Mock TenableIO
    mock_tio.scans.list.return_value = [
        {"uuid": "uuid1", "name": "Test Scan 1", "schedule_uuid": "sched1", "id": 1},
    ]
    mock_tio.scans.history.return_value = [
        {"id": "h1", "status": "running", "time_end": CURRENT_TIME - 100},
    ]
    config = Config(scan_name="Test Scan", allowed_memory_gb=2,
                    window=MagicMock(since=CURRENT_TIME - 3600, upto=CURRENT_TIME))

    fetcher = ScansFetcher(mock_tio)
    histories = fetcher.scan_histories(config)

    assert len(histories) == 0


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_scans_by_name_with_multiple_comma_separated_names(mock_tio):
    # Mock TenableIO
    mock_tio.scans.list.return_value = [
        {"uuid": "uuid1", "name": "First Scan", "schedule_uuid": "sched1", "id": 1},
        {"uuid": "uuid2", "name": "Second Scan", "schedule_uuid": "sched2", "id": 2},
        {"uuid": "uuid3", "name": "Third Scan", "schedule_uuid": "sched3", "id": 3},
    ]
    config = Config(scan_name="First,Third", allowed_memory_gb=2)

    fetcher = ScansFetcher(mock_tio)
    scans = fetcher._scans_by_name(config)

    assert len(scans) == 2
    assert Scan(uuid="uuid1", name="First Scan", schedule_uuid="sched1", id=1) in scans
    assert Scan(uuid="uuid3", name="Third Scan", schedule_uuid="sched3", id=3) in scans


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_scans_by_name_with_whitespace_and_case_insensitivity(mock_tio):
    # Mock TenableIO
    mock_tio.scans.list.return_value = [
        {"uuid": "uuid1", "name": "Test Scan 1", "schedule_uuid": "sched1", "id": 1},
        {"uuid": "uuid2", "name": "Another Scan", "schedule_uuid": "sched2", "id": 2},
    ]
    config = Config(scan_name="  test scan  ,  ANOTHER SCAN  ", allowed_memory_gb=2)

    fetcher = ScansFetcher(mock_tio)
    scans = fetcher._scans_by_name(config)

    assert len(scans) == 2
    assert Scan(uuid="uuid1", name="Test Scan 1", schedule_uuid="sched1", id=1) in scans
    assert Scan(uuid="uuid2", name="Another Scan", schedule_uuid="sched2", id=2) in scans


@patch("tvm_multi_scan_exporter.scan_fetcher.TenableIO")
def test_scans_by_name_no_matches(mock_tio):
    # Mock TenableIO
    mock_tio.scans.list.return_value = [
        {"uuid": "uuid1", "name": "Test Scan 1", "schedule_uuid": "sched1", "id": 1},
    ]
    config = Config(scan_name="NonExistent, Other", allowed_memory_gb=2)

    fetcher = ScansFetcher(mock_tio)
    scans = fetcher._scans_by_name(config)

    assert len(scans) == 0

