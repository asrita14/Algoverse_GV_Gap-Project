#!/usr/bin/env python3
import os, time, json, argparse, re, requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True) or ".env")
FINAL_RE = re.compile(r"Final:\s*(.+)")

def messages_for(q: str):
    sys = "You are a careful problem solver. Show steps briefly and end with 'Final: <answer>'."
    usr = f"Question: {q}\nSolve step by step. Conclude with 'Final: <answer>'."
    return [{"role":"system","content":sys},{"role":"user","content":usr}]

def call_openai(model, messages):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    t0=time.time()
    r = client.chat.completions.create(model=model, messages=messages, temperature=0.0)
    return r.choices[0].message.content, time.time()-t0, getattr(r,"usage",{}) or {}

def call_together(model, messages):
    url="https://api.together.xyz/v1/chat/completions"
    headers={"Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}", "Content-Type":"application/json"}
    t0=time.time()
    r=requests.post(url,json={"model":model,"messages":messages,"temperature":0.0},headers=headers); r.raise_for_status()
    d=r.json(); return d["choices"][0]["message"]["content"], time.time()-t0, d.get("usage",{})

def parse_final(text: str):
    m=FINAL_RE.search(text or ""); return (m.group(1).strip() if m else text.strip()) or ""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", choices=["openai","together"], default=os.getenv("PROVIDER","openai"))
    ap.add_argument("--model", default=os.getenv("MODEL_SMALL","gpt-4o-mini"))
    args=ap.parse_args()

    Path(Path(args.out).parent).mkdir(parents=True, exist_ok=True)
    with open(args.inp,"r",encoding="utf-8") as fin, open(args.out,"w",encoding="utf-8") as fout:
        for line in fin:
            ex=json.loads(line)
            msgs=messages_for(ex["question"])
            if args.provider=="openai": text,dt,usage=call_openai(args.model,msgs)
            else:                       text,dt,usage=call_together(args.model,msgs)
            rec={
              "id":ex["id"],"domain":ex["domain"],"dataset":ex["dataset"],"split":ex["split"],
              "question":ex["question"],
              "generator":{"provider":args.provider,"model":args.model,"temperature":0.0},
              "gen":{"cot":text,"answer":parse_final(text),"latency_s":round(dt,3),
                     "tokens_in":usage.get("prompt_tokens") or usage.get("prompt_tokens_total"),
                     "tokens_out":usage.get("completion_tokens") or usage.get("generation_tokens"),
                     "cost_usd":None}
            }
            fout.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(f"Wrote → {args.out}")

if __name__=="__main__": main()
