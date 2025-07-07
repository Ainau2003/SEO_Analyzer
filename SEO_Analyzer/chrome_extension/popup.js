document.getElementById('analyzeBtn').addEventListener('click', function () {
  const keyword = document.getElementById('keywordInput').value.trim();
  const resultsDiv = document.getElementById('results');

  if (!keyword) {
    resultsDiv.innerHTML = '<p style="color:red;">Enter a keyword</p>';
    return;
  }

  resultsDiv.innerHTML = 'Analyzing...';

  fetch(`http://localhost:5000/seo?q=${encodeURIComponent(keyword)}`)
    .then(res => res.json())
    .then(data => {
      const best = data.summary.best_keyword;
      resultsDiv.innerHTML = `
        <p><strong>Keyword:</strong> ${best.keyword}</p>
        <p><strong>Volume:</strong> ${best.search_volume}</p>
        <p><strong>CPC:</strong> $${best.cpc}</p>
        <p><strong>Trend:</strong> ${best.trend}</p>
        <p><strong>Difficulty:</strong> ${best.difficulty}</p>
      `;
    })
    .catch(err => {
      resultsDiv.innerHTML = '<p style="color:red;">Error fetching data</p>';
      console.error(err);
    });
});