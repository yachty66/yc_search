import { GoogleGenerativeAI } from "@google/generative-ai";
import { createClient } from "@supabase/supabase-js";

// Initialize the Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

// Initialize the model
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

function get_prompt(query, data) {
  return `
        You get as input all the rows of a database with all companies which ever took part of YC. You are given a query from a user and you must return the IDs of the companies that match the query. Here is the query:

        ${query}

        Return the IDs of the companies that match the query.

        Here is the database:

        ---
        ${data}
        ---

        It is possible that the query has no results; in this case, return an empty array. You must return your result in JSON format like this:

        {"response": [201, 202, 203]}

        Return the IDs of the companies that match the query in JSON format:
    `;
}

async function get_database_data() {
  //this does not include the ids from the entries
  const { data, error } = await supabase.rpc("get_all_startuprxiv_data");
  if (error) throw error;
  const processedData = data.map((item) => ({
    id: item.id,
    ...item,
  }));
  return JSON.stringify(processedData, null, 2);
}

function get_clean_json(rawResponse) {
  const cleanJson = rawResponse
    .replace(/```json\n/, "")
    .replace(/\n```/, "")
    .trim();
  return JSON.parse(cleanJson);
}

async function get_company_data(companyIds) {
  try {
    const { data, error } = await supabase.rpc("get_startuprxiv_by_ids", {
      ids: companyIds,
    });

    if (error) throw error;
    return data;
  } catch (error) {
    console.error("Error fetching company data:", error);
    throw error;
  }
}

export default async function handler(req, res) {
  const { query } = req.body;
  console.log("Getting database rows for query:", query);

  const database_data = await get_database_data();
  //   console.log("Database data: ", database_data);

  const prompt = get_prompt(query, database_data);
  console.log("Prompt: ", prompt);
  const result = await model.generateContent(prompt);
  const companyIds = get_clean_json(await result.response.text()).response;
  console.log("Company IDs:", companyIds);
  const companyData = await get_company_data(companyIds);
  console.log("Company Data:", companyData);
  //now i can input the ids into a supabase sql query
  return res.status(200).json(companyData);
}
