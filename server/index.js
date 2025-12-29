import express from "express";
import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(express.json());

app.post("/ask", async (req, res) => {
  const { prompt } = req.body;

  try {
    const response = await fetch(
      "https://router.huggingface.co/hf-inference/models/gpt2",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.HF_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          inputs: `Explain this legal text in very simple language:\n${prompt}`,
          parameters: {
            max_new_tokens: 150,
          },
        }),
      }
    );

    const rawText = await response.text(); // 👈 FIX

    // Try parsing JSON safely
    let data;
    try {
      data = JSON.parse(rawText);
    } catch {
      console.error("HF RAW RESPONSE:", rawText);
      return res.status(500).json({
        error: "HF returned non-JSON response",
        details: rawText,
      });
    }

    if (!response.ok) {
      return res.status(500).json({
        error: "HF API failed",
        details: data,
      });
    }

    res.json({
      answer: data[0]?.generated_text || "No response generated",
    });
  } catch (err) {
    console.error("Server error:", err);
    res.status(500).json({ error: "Server crashed", details: err.message });
  }
});

app.listen(5000, () => {
  console.log("✅ Server running on http://localhost:5000");
});
