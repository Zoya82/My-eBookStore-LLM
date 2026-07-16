import { request } from './client.js'
const fields=['receiver','phone','province','city','district','detail','is_default']
const clean=payload=>Object.fromEntries(fields.filter(key=>Object.prototype.hasOwnProperty.call(payload||{},key)).map(key=>[key,typeof payload[key]==='string'?payload[key].trim():payload[key]]))
const list=response=>response?.data ?? response
export async function getAddresses(){return list(await request('/users/addresses/'))}
export async function createAddress(payload){return list(await request('/users/addresses/',{method:'POST',body:clean(payload)}))}
export async function updateAddress(id,payload){if(!Number.isInteger(Number(id))||Number(id)<=0)throw new Error('地址 ID 无效');return list(await request(`/users/addresses/${id}/`,{method:'PUT',body:clean(payload)}))}
export async function deleteAddress(id){if(!Number.isInteger(Number(id))||Number(id)<=0)throw new Error('地址 ID 无效');return list(await request(`/users/addresses/${id}/`,{method:'DELETE'}))}
