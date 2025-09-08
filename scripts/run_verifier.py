#!/usr/bin/env python3
import os, time, json, argparse, requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True) or ".env")
INSTR='Return JSON: {"label":"accept|reject","confidence":0.xx,"rationale":"..."}'

def judge_messages(q, ans, cot):
    return [
      {"role":"system","content":"You judge if a final answer is correct."},
      {"role":"user","content":f"Question: {q}\nFinal answer: {ans}\nSteps (may be empty):\n{cot or ''}\n{INSTR}"}
    ]

def call_openai(model,messages):
    from openai import OpenAI
    c=OpenAI(api_key=os.getenv("OPENAI_API_KEY")); t0=time.time()
    r=c.chat.completions.create(model=model,messages=messages,temperature=0.0)
    return r.choices[0].message.content, time.time()-t0

def call_together(model,messages):
    url="https://api.together.xyz/v1/chat/completions"
    h={"Authorization":f"Bearer {os.getenv('TOGETHER_API_KEY')}","Content-Type":"application/json"}
    t0=time.time(); r=requests.post(url,json={"model":model,"messages":messages,"temperature":0.0},headers=h); r.raise_for_status()
    d=r.json(); return d["choices"][0]["message"]["content"], time.time()-t0

def safe_parse(s: str):
    try:
        j=json.loads(s); lab=j.get("label","").strip().lower(); conf=float(j.get("confidence",0)); rat=j.get("rationale","")
        if lab not in {"accept","reject"}: raise ValueError
        return {"label":lab,"confidence":max(0,min(1,conf)),"rationale":rat}
    except Exception:
        return {"label":"reject","confidence":0.0,"rationale":"invalid JSON"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in",dest="inp",required=True)   # 01_gen.jsonl
    ap.add_argument("--out",required=True)             # 02_verify.jsonl
    ap.add_argument("--ref",required=True)             # processed jsonl (not required for prompt; kept for future)
    ap.add_argument("--provider",choices=["openai","together"],default=os.getenv("PROVIDER","openai"))
    ap.add_argument("--model",default=os.getenv("MODEL_SMALL","gpt-4o-mini"))
    args=ap.parse_args()

    Path(Path(args.out).parent).mkdir(parents=True, exist_ok=True)
    with open(args.inp,"r",encoding="utf-8") as fin, open(args.out,"w",encoding="utf-8") as fout:
        for line in fin:
            rec=json.loads(line)
            q=rec.get("question",""); ans=rec["gen"]["answer"]; cot=rec["gen"]["cot"]
            msgs=judge_messages(q,ans,cot)
            txt,dt=(call_openai if args.provider=="openai" else call_together)(args.model,msgs)
            v=safe_parse(txt)
            rec["verify"]={"label":v["label"],"confidence":v["confidence"],"rationale":v["rationale"],"latency_s":round(dt,3)}
            fout.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(f"Wrote → {args.out}")

if __name__=="__main__": main()
