- 配置文件 eap_user
``` bash
第一行协商 phase 1 的认证方法顺序
第二行协商 phase 2 的认证方法顺序
*               PEAP,TLS,TTLS
"testuser"      MSCHAPV2,TTLS-CHAP,TTLS-MSCHAP,MD5,TTLS-MSCHAPV2 "password" [2]
```
