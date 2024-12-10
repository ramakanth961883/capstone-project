document.getElementById("tweet-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const query = document.getElementById("query").value;
    const language = document.getElementById("language").value;
    const retweetOption = document.getElementById("retweet_option").value;
    const numTweets = document.getElementById("num_tweets").value;
    const resultsDiv = document.getElementById("results");
    const resultsBody = document.getElementById("results-body");

    let searchQuery = query;
    if (retweetOption === "no") {
        searchQuery += " -is:retweet";
    }
    searchQuery += ` lang:${language}`;

    resultsDiv.style.display = "block";
    resultsBody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

    const formData = new FormData();
    formData.append("query", searchQuery);
    formData.append("num_tweets", numTweets);

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.error) {
            resultsBody.innerHTML = `<tr><td colspan="6" class="text-danger text-center">Error: ${data.error}</td></tr>`;
        } else {
            resultsBody.innerHTML = ""; // Clear loading message
            data.tweets.forEach((tweet, index) => {
                const transformerSentimentClass =
                    tweet.transformer_sentiment === "POSITIVE"
                        ? "text-success"
                        : tweet.transformer_sentiment === "NEGATIVE"
                        ? "text-danger"
                        : "text-warning";

                const lstmSentimentClass =
                    tweet.lstm_sentiment === "POSITIVE"
                        ? "text-success"
                        : "text-danger";

                const row = `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${tweet.text}</td>
                        <td class="${transformerSentimentClass}">${tweet.transformer_sentiment}</td>
                        <td>${tweet.transformer_score.toFixed(2)}</td>
                        <td class="${lstmSentimentClass}">${tweet.lstm_sentiment}</td>
                        <td>${tweet.lstm_score.toFixed(2)}</td>
                    </tr>
                `;
                resultsBody.innerHTML += row;
            });
        }
    } catch (error) {
        resultsBody.innerHTML = `<tr><td colspan="6" class="text-danger text-center">An error occurred. Please try again later.</td></tr>`;
    }
});
