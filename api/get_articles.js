import mongoose from "mongoose";

const MONGO_URI = process.env.MONGO_URI;
let isConnected;

export default async function handler(req, res) {
    try {
        if (!MONGO_URI) {
            return res.status(500).json({ error: "MongoDB URI is missing" });
        }

        // Connect to MongoDB if not already connected
        if (isConnected) {
            console.log("Using existing MongoDB connection");
        } else {
            console.log("Connecting to MongoDB...");
            await mongoose.connect(MONGO_URI, {
                useNewUrlParser: true,
                useUnifiedTopology: true,
            });
            isConnected = true;
            console.log("Connected to MongoDB");
        }

        const db = mongoose.connection.db;
        const collection = db.collection("news_articles");

        // Check for search query
        const { q } = req.query; // Retrieve the search query from the request
        let articles;

        if (q) {
            // Perform search based on keywords in the title or the keywords array
            articles = await collection.find({
                $or: [
                    { title: { $regex: q, $options: "i" } }, // Case-insensitive search in title
                    { keywords: { $in: [new RegExp(q, "i")] } } // Case-insensitive search in keywords array
                ]
            }).sort({ time: -1 }).toArray();
        } else {
            // If no query is provided, retrieve all articles
            articles = await collection.find().sort({ time: -1 }).toArray();
        }
        

        console.log("Retrieved articles:", articles); // Log retrieved articles
        res.status(200).json(articles);
    } catch (error) {
        console.error("Internal Server Error:", error); // Log the error message
        return res.status(500).json({ error: error.message || "Internal Server Error" });
    }
}