import { GoogleGenerativeAI } from "@google/generative-ai";
import fs from "fs";
import path from "path";

function get_prompt(query, data) {
  return `
        You get as input all the rows of a database with all companies which ever took part of YC. You are given a query from a user and you must return the IDs of the companies that match the query. Here is the query:

        ---
        ${query}
        ---

        Return the exact names of the companies that match the query. The names of the companies must be taken from the value of the key "company_name" in the database.

        Here is the database:

        ---
        ${data}
        ---

        It is possible that the query has no results; in this case, return an empty array. You must return your result in JSON format like this:

        {"response": ["Company A", "Company B", "Company C"]}

        Return the names of the companies that match the query in JSON format:
    `;
}

function get_clean_json(rawResponse) {
  const cleanJson = rawResponse
    .replace(/```json\n/, "")
    .replace(/\n```/, "")
    .trim();
  return JSON.parse(cleanJson);
}

async function get_company_data(companyNames, allCompanies) {
  return allCompanies.filter((company) =>
    companyNames.includes(company.company_name)
  );
}

async function processPartialData(query, jsonData, apiKey) {
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  
  const prompt = get_prompt(query, JSON.stringify(jsonData, null, 2));
  const result = await model.generateContent(prompt);
  const response = await result.response.text();
  return get_clean_json(response).response;
}

export default async function handler(req, res) {
  try {
    const { query, apiKey } = req.body;
    
    if (!apiKey) {
      return res.status(400).json({ error: "API key is required" });
    }

    console.log("Getting companies for query:", query);

    const filePath1 = path.join(process.cwd(), "data/all_part1.json");
    const filePath2 = path.join(process.cwd(), "data/all_part2.json");
    
    const jsonData1 = JSON.parse(fs.readFileSync(filePath1, "utf8"));
    const jsonData2 = JSON.parse(fs.readFileSync(filePath2, "utf8"));
    const allCompanies = [...jsonData1, ...jsonData2];

    const [companyNames1, companyNames2] = await Promise.all([
      processPartialData(query, jsonData1, apiKey),
      processPartialData(query, jsonData2, apiKey)
    ]);

    const allCompanyNames = [...new Set([...companyNames1, ...companyNames2])];
    const matchedCompanies = await get_company_data(allCompanyNames, allCompanies);
    
    return res.status(200).json(matchedCompanies);
  } catch (error) {
    console.error("Error processing query:", error);
    return res.status(500).json({ 
      error: error.message || "Internal server error"
    });
  }
}
