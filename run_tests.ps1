pytest tests/ -v --tb=line 2>&1 | Tee-Object -FilePath test_output.txt | Select-Object -Last 300
