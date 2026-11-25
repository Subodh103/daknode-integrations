import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DakNodeToolkit, ToolkitRefused } from '../dist/index.js';
import { createVercelTools } from '../dist/vercel.js';
import { createLangChainTools } from '../dist/langchain.js';

const inbox='11111111-1111-4111-8111-111111111111',other='22222222-2222-4222-8222-222222222222';
const key='synthetic-private-value';
function fixture(handler,extra={}) {
  const requests=[];
  const options={apiKey:key,inboxId:inbox,...extra,fetch:async request=>{
    requests.push(request);
    assert.equal(request.headers.get('authorization'),`Bearer ${key}`);
    assert.equal(request.redirect,'error');
    assert.equal(request.credentials,'omit');
    const value=await handler?.(request);
    if(value) return value;
    if(new URL(request.url).pathname==='/v1/mcp/identity') return Response.json({inbox_id:inbox,private_provider_metadata:'not-for-setup-output'});
    return Response.json({id:inbox,inbox_id:inbox,items:[],has_more:false,next_cursor:null});
  }};
  return {options,requests,toolkit:new DakNodeToolkit(options)};
}
const refused=code=>error=>error instanceof ToolkitRefused && error.code===code && !error.message.includes(key);

test('construction is offline, core defaults are read-only, setup result is minimal',async()=>{
  const {toolkit,requests}=fixture();
  assert.equal(requests.length,0);
  assert.equal(toolkit.definitions().length,6);
  assert.ok(!toolkit.definitions().some(t=>t.name==='send'));
  assert.deepEqual(await toolkit.checkConnection(),{authenticated:true,scope:'inbox',inboxId:inbox,writes:[],sendingPolicy:'review'});
});
test('real Vercel tools register and execute without any model calls',async()=>{
  const {options,requests}=fixture();
  const tools=createVercelTools(options);
  assert.equal(requests.length,0);
  assert.equal(Object.keys(tools).length,6);
  assert.ok(tools.daknode_list_messages.inputSchema);
  const result=await tools.daknode_list_messages.execute({limit:3},{toolCallId:'fixture',messages:[]});
  assert.equal(result.inbox_id,inbox);
  assert.equal(new URL(requests[1].url).searchParams.get('limit'),'3');
});
test('real LangChain tools validate schema and execute SDK-backed functions',async()=>{
  const {options,requests}=fixture();
  const tools=createLangChainTools(options);
  assert.equal(requests.length,0);
  const tool=tools.find(t=>t.name==='daknode_list_threads');
  assert.equal(JSON.parse(await tool.invoke({limit:2})).inbox_id,inbox);
  assert.ok(tool.schema);
});
test('Vercel per-call cancellation reaches the SDK transport boundary',async()=>{
  const {options,requests}=fixture();
  const tool=createVercelTools(options).daknode_list_messages;
  const controller=new AbortController();controller.abort();
  await assert.rejects(tool.execute({}, {toolCallId:'fixture',messages:[],abortSignal:controller.signal}),refused('aborted'));
  assert.equal(requests.length,0);
});
test('every call rechecks identity, including revocation after a successful call',async()=>{
  let revoked=false;
  const {toolkit,requests}=fixture(request=>new URL(request.url).pathname==='/v1/mcp/identity' ? Response.json({inbox_id:revoked?other:inbox}):null);
  await toolkit.execute('list_messages',{});
  revoked=true;
  await assert.rejects(toolkit.execute('list_messages',{}),refused('scope_denied'));
  assert.equal(requests.length,3);
});
test('workspace keys cannot widen this inbox-scoped toolkit',async()=>{
  const {toolkit,requests}=fixture(()=>Response.json({inbox_id:null}));
  await assert.rejects(toolkit.execute('search',{query:'invoice'}),refused('scope_denied'));
  assert.equal(requests.length,1);
});
test('strict bounded input validation runs even for direct execute calls',async()=>{
  const {toolkit,requests}=fixture();
  for(const input of [{inbox_id:other},{limit:11},{limit:1.5},{cursor:'x'.repeat(4097)},{base_url:'https://untrusted.test'}]) {
    await assert.rejects(toolkit.execute('list_messages',input),refused('invalid_input'));
  }
  await assert.rejects(toolkit.execute('approval',{}),refused('invalid_input'));
  assert.equal(requests.length,0);
});
test('resource reads and writes refuse cross-inbox data',async()=>{
  const {toolkit,requests}=fixture(request=>new URL(request.url).pathname.includes('/drafts/')?Response.json({inbox_id:other}):null,{writes:['cancel_draft']});
  await assert.rejects(toolkit.execute('cancel_draft',{draft_id:inbox,expected_revision:other}),refused('scope_denied'));
  assert.ok(requests.every(r=>r.method==='GET'));
});
test('draft writes preserve approval and exact observed revision',async()=>{
  const {toolkit,requests}=fixture(undefined,{writes:['create_draft','update_draft','cancel_draft']});
  const message={to:'recipient@example.test',subject:'Fixture',body_text:'Untrusted mail'};
  await toolkit.execute('create_draft',message);
  assert.equal((await requests.at(-1).clone().json()).require_human_approval,true);
  await toolkit.execute('update_draft',{...message,draft_id:inbox,expected_revision:other});
  assert.deepEqual(await requests.at(-1).clone().json(),{message:{inbox_id:inbox,...message},require_human_approval:true,expected_revision:other});
});
test('send is absent and refused unless the application explicitly enables direct policy',async()=>{
  assert.throws(()=>fixture(undefined,{writes:['send']}),/explicit application-owned direct policy/);
  const {toolkit,requests}=fixture();
  await assert.rejects(toolkit.execute('send',{to:'a@example.test',subject:'s',body_text:'b',idempotency_key:'once'}),refused('write_disabled'));
  assert.equal(requests.length,0);
});
test('model inputs cannot disable draft approval or change private configuration',async()=>{
  const {toolkit,requests}=fixture(undefined,{writes:['create_draft']});
  const mail={to:'a@example.test',subject:'s',body_text:'b'};
  for(const extra of [{require_human_approval:false},{sendingPolicy:'direct'},{apiKey:key},{inbox_id:other}]) {
    await assert.rejects(toolkit.execute('create_draft',{...mail,...extra}),refused('invalid_input'));
  }
  assert.equal(requests.length,0);
});
test('direct writes preserve idempotency exactly and never retry provider refusals',async()=>{
  const {toolkit,requests}=fixture(request=>request.method==='POST'?Response.json({private:key},{status:503}):null,{writes:['send'],sendingPolicy:'direct'});
  await assert.rejects(toolkit.execute('send',{to:'a@example.test',subject:'s',body_text:'b',idempotency_key:'retain-exactly'}),refused('http_refused'));
  assert.equal(requests.filter(r=>r.method==='POST').length,1);
  assert.equal(requests.at(-1).headers.get('idempotency-key'),'retain-exactly');
  await assert.rejects(toolkit.execute('send',{to:'a@example.test',subject:'s',body_text:'b',idempotency_key:' retain-exactly '}),refused('invalid_input'));
  assert.equal(requests.filter(r=>r.method==='POST').length,1);
});
test('private error bodies and provider-supplied toolkit headers are never exposed',async()=>{
  const {toolkit}=fixture(()=>Response.json({private:key},{status:403,headers:{'x-daknode-toolkit-refusal':'secret'}}));
  await assert.rejects(toolkit.checkConnection(),error=>refused('http_refused')(error)&&error.status===403&&!error.message.includes('secret'));
});
test('inert mail text is bounded and visibly truncated',async()=>{
  const {toolkit}=fixture(request=>new URL(request.url).pathname.endsWith('/messages')?Response.json({items:[{text:'<script>'+ 'x'.repeat(5000)}]}):null);
  const value=await toolkit.execute('list_messages',{});
  assert.ok(value.items[0].text.endsWith('[truncated]'));
});
test('streamed response bytes are limited without trusting content-length',async()=>{
  let cancelled=false;
  const {toolkit}=fixture(()=>new Response(new ReadableStream({pull(c){c.enqueue(new Uint8Array(600000));},cancel(){cancelled=true;}})));
  await assert.rejects(toolkit.checkConnection(),refused('output_limit'));
  assert.equal(cancelled,true);
});
test('final tool output cannot exceed the declared budget',async()=>{
  const {toolkit}=fixture(request=>new URL(request.url).pathname.endsWith('/messages')?Response.json({items:Array.from({length:10},()=>({text:'x'.repeat(3900)}))}):null);
  await assert.rejects(toolkit.execute('list_messages',{}),refused('output_limit'));
});
test('deadline covers a stalled provider response body and cancels it',async()=>{
  let cancelled=false;
  const {toolkit}=fixture(()=>new Response(new ReadableStream({cancel(){cancelled=true;}})),{timeoutMs:15});
  await assert.rejects(toolkit.checkConnection(),refused('aborted'));
  assert.equal(cancelled,true);
});
test('caller cancellation prevents transport calls',async()=>{
  const controller=new AbortController();controller.abort();
  const {toolkit,requests}=fixture(undefined,{signal:controller.signal});
  await assert.rejects(toolkit.checkConnection(),refused('aborted'));
  assert.equal(requests.length,0);
});
test('invalid base origins cannot receive a private credential',()=>{
  for(const baseUrl of ['http://public.example','https://user:pass@example.test','https://api.example.test/path','https://api.example.test/?key=value']) assert.throws(()=>fixture(undefined,{baseUrl}));
});
