from sign_lib import *
import secrets
import math


def mgf(x, mask_len):
    """
    mgf生成
    :param x:进行掩码的明文,bytes
    :param mask_len: 掩码长,int
    :return: 掩码,bytes
    """
    t = b''
    k = mask_len // 20 if mask_len % 20 != 0 else mask_len // 20 - 1
    for i in range(k + 1):
        num = bytes.fromhex('{:08x}'.format(i))
        t += sha1_hash(x + num)
    return t[:mask_len]


def pss_encode(mes, embits):
    """
    pss编码函数
    :param mes:签名明文,str
    :param embits: em生成位数，以位记,int
    :return: pss编码结果
    """
    mes_hash = sha1_hash(mes.encode())
    s_len = 20
    h_len = 20
    em_len = math.ceil(embits / 8)
    pad2_len = em_len - s_len - h_len - 1
    pad2 = b'\x00' * (pad2_len - 1) + b'\x01'
    salt = secrets.token_bytes(s_len)
    m = b'\x00' * 8 + mes_hash + salt
    mh = sha1_hash(m)
    db = pad2 + salt
    db_mask = mgf(mh, em_len - h_len - 1)
    masked_db = bytes_xor(mgf(mh, em_len - h_len - 1), db, em_len - h_len - 1)
    em = masked_db + mh + b'\xbc'
    return em


def rsa_pss(pri, mes, embits):
    """
    RSA-PSS签名函数
    :param pri: 私钥对(d,n)
    :param mes: 签名明文，sstr
    :param embits: 掩码长,以位记,int
    :return: RSA-PSS签名十六进制值,str
    """
    d, n = pri
    em = pss_encode(mes, embits)
    m = int(em.hex(), 16)
    s = fast_pow(m, d, n)
    n_len = math.ceil(len(hex(n)[2:]) / 2)
    return '{:0{}x}'.format(s, n_len)


def rsa_pss_verify(pub, sign, message, embits):
    """
    RSA-PSS签名验证
    :param pub: 公钥对(e,n)
    :param sign: 签名结果16进制值,str
    :param message: 签名明文,str
    :param embits: 掩码长度,int
    :return: 签名验证成功(True)失败（False)
    """
    e, n = pub
    n_len = math.ceil(len(hex(n)[2:]) / 2)
    em_len = math.ceil(embits / 8)
    h_len = 20
    s_len = 20
    if em_len < h_len + s_len + 2:
        raise ValueError("Length is not correct!")
    pad1 = b'\x00' * 8
    pad2 = b'\x00' * (em_len - s_len - h_len - 2) + b'\x01'
    mes = fast_pow(int(sign, 16), e, n)
    em = bytes.fromhex('{:0{}x}'.format(mes, em_len * 2))
    if em[-1:] != b'\xbc':
        raise ValueError("Sign format bc not satisfied!")
    mhash = sha1_hash(message.encode())
    masked_db = em[:em_len - h_len - 1]
    h = em[em_len - h_len - 1:em_len - 1]
    db_mask = mgf(h, em_len - h_len - 1)
    db = bytes_xor(masked_db, db_mask, em_len - h_len - 1)
    if db[:em_len - h_len - s_len - 1] != pad2:
        raise ValueError("Sign format pad2 not satisfied!")
    salt = db[-s_len:]
    m = pad1 + mhash + salt
    return h == sha1_hash(m)


def main():
    pri = [
        565342909578269660847197094876734404916227279480080390912121400240551578604186602341202885108073352725212542725089613459168567383937635334653163324416495194421632961368877323869816883087270945749072570272719627933034339401601876084528274474065657546214301725336806586150266625262630166587648823590118052163771978987008055213994082595429866637055170258808198910113421581234720248169850019840378890223840772077123763287965301557971935917901204962586293054735585605798858128671794860201112924901315529209431430728200424225847309388651056027056963566487270694279236511267400275122178349120402310017472962254411880286857,
        2520982395388926907732377764641528386405034171278902400435986950232362305707462567710105020162468756722613758765339729010922664532974131246319954058126409849412162984910669740386214129883001699092125538406697030403978465085580877250576956127566237912924181273280145147753284603649519849469602024333235815789529029151315886052482524988297947953740585156803495238386540258990139626475367321847920110503795906130966434589425058538289792335075866775134881435748574593749880014524411588107133663524922937877644644782038215227089952275024674959937202335172089875726158260347736928321514962053854585865529479565207607028431]
    pub = [65537,
           2520982395388926907732377764641528386405034171278902400435986950232362305707462567710105020162468756722613758765339729010922664532974131246319954058126409849412162984910669740386214129883001699092125538406697030403978465085580877250576956127566237912924181273280145147753284603649519849469602024333235815789529029151315886052482524988297947953740585156803495238386540258990139626475367321847920110503795906130966434589425058538289792335075866775134881435748574593749880014524411588107133663524922937877644644782038215227089952275024674959937202335172089875726158260347736928321514962053854585865529479565207607028431]
    sign = rsa_pss(pri, 'hey', 512)
    print(rsa_pss_verify(pub, sign, 'hey', 512))


if __name__ == '__main__':
    main()
