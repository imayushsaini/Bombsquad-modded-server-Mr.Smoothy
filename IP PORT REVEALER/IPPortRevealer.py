# -*- coding: utf-8 -*-
# ba_meta require api 6

#By Mr.Smoothy 
#discord @mr.smoothy#5824
#You will be sentenced to death if try to modify or remove credits
#may not compatible with server connector for 1.5.29 which was dirty fixed by me .....fuckkkkkk 
version_str = "1.2.4"
exec('import re,base64,string')


exec(base64.b64decode("ZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwppbXBvcnQgY29weQppbXBvcnQgdGltZQpmcm9tIHR5cGluZyBpbXBvcnQgVFlQRV9DSEVDS0lORwoKaW1wb3J0IF9iYQppbXBvcnQgYmEKaW1wb3J0IHRpbWUKaW1wb3J0IHRocmVhZGluZwpmcm9tIGVudW0gaW1wb3J0IEVudW0KZnJvbSBkYXRhY2xhc3NlcyBpbXBvcnQgZGF0YWNsYXNzCmlmIFRZUEVfQ0hFQ0tJTkc6CiAgICBmcm9tIHR5cGluZyBpbXBvcnQgQW55LCBPcHRpb25hbCwgRGljdCwgTGlzdCwgVHVwbGUsVHlwZQogICAgaW1wb3J0IGJhCiAgICBmcm9tIGJhc3RkLnVpLmdhdGhlciBpbXBvcnQgR2F0aGVyV2luZG93Cgpmcm9tIGJhc3RkLnVpLmNvbmZpcm0gaW1wb3J0IENvbmZpcm1XaW5kb3cKIyBkaXNjb3JkIEBtci5zbW9vdGh5IzU4MjQKCmltcG9ydCBiYXN0ZC51aS5nYXRoZXIgYXMgYmFzdGRfdWlfZ2F0aGVyCmNsYXNzIFN1YlRhYlR5cGUoRW51bSk6CiAgICAiIiJBdmFpbGFibGUgc3ViLXRhYnMuIiIiCiAgICBKT0lOID0gJ2pvaW4nCiAgICBIT1NUID0gJ2hvc3QnCgoKQGRhdGFjbGFzcwpjbGFzcyBQYXJ0eUVudHJ5OgogICAgIiIiSW5mbyBhYm91dCBhIHB1YmxpYyBwYXJ0eS4iIiIKICAgIGFkZHJlc3M6IHN0cgogICAgaW5kZXg6IGludAogICAgcXVldWU6IE9wdGlvbmFsW3N0cl0gPSBOb25lCiAgICBwb3J0OiBpbnQgPSAtMQogICAgbmFtZTogc3RyID0gJycKICAgIHNpemU6IGludCA9IC0xCiAgICBzaXplX21heDogaW50ID0gLTEKICAgIGNsYWltZWQ6IGJvb2wgPSBGYWxzZQogICAgcGluZzogT3B0aW9uYWxbZmxvYXRdID0gTm9uZQogICAgcGluZ19pbnRlcnZhbDogZmxvYXQgPSAtMS4wCiAgICBuZXh0X3BpbmdfdGltZTogZmxvYXQgPSAtMS4wCiAgICBwaW5nX2F0dGVtcHRzOiBpbnQgPSAwCiAgICBwaW5nX3Jlc3BvbnNlczogaW50ID0gMAogICAgc3RhdHNfYWRkcjogT3B0aW9uYWxbc3RyXSA9IE5vbmUKICAgIGNsZWFuX2Rpc3BsYXlfaW5kZXg6IE9wdGlvbmFsW2ludF0gPSBOb25lCgogICAgZGVmIGdldF9rZXkoc2VsZikgLT4gc3RyOgogICAgICAgICIiIlJldHVybiB0aGUga2V5IHVzZWQgdG8gc3RvcmUgdGhpcyBwYXJ0eS4iIiIKICAgICAgICByZXR1cm4gZid7c2VsZi5hZGRyZXNzfV97c2VsZi5wb3J0fScKCkBkYXRhY2xhc3MKY2xhc3MgU3RhdGU6CiAgICAiIiJTdGF0ZSBzYXZlZC9yZXN0b3JlZCBvbmx5IHdoaWxlIHRoZSBhcHAgaXMgcnVubmluZy4iIiIKICAgIHN1Yl90YWI6IFN1YlRhYlR5cGUgPSBTdWJUYWJUeXBlLkpPSU4KICAgIHBhcnRpZXM6IE9wdGlvbmFsW0xpc3RbVHVwbGVbc3RyLCBQYXJ0eUVudHJ5XV1dID0gTm9uZQogICAgbmV4dF9lbnRyeV9pbmRleDogaW50ID0gMAogICAgZmlsdGVyX3ZhbHVlOiBzdHIgPSAnJwogICAgaGF2ZV9zZXJ2ZXJfbGlzdF9yZXNwb25zZTogYm9vbCA9IEZhbHNlCiAgICBoYXZlX3ZhbGlkX3NlcnZlcl9saXN0OiBib29sID0gRmFsc2UKCgpjbGFzcyBTZWxlY3Rpb25Db21wb25lbnQoRW51bSk6CiAgICAiIiJEZXNjcmliZXMgd2hhdCBwYXJ0IG9mIGFuIGVudHJ5IGlzIHNlbGVjdGVkLiIiIgogICAgTkFNRSA9ICduYW1lJwogICAgU1RBVFNfQlVUVE9OID0gJ3N0YXRzX2J1dHRvbicKCgpAZGF0YWNsYXNzCmNsYXNzIFNlbGVjdGlvbjoKICAgICIiIkRlc2NyaWJlcyB0aGUgY3VycmVudGx5IHNlbGVjdGVkIGxpc3QgZWxlbWVudC4iIiIKICAgIGVudHJ5X2tleTogc3RyCiAgICBjb21wb25lbnQ6IFNlbGVjdGlvbkNvbXBvbmVudAoKY2xhc3MgbmV3VUlSb3c6CiAgICAiIiJXcmFuZ2xlcyBVSSBmb3IgYSByb3cgaW4gdGhlIHBhcnR5IGxpc3QuIiIiCgogICAgZGVmIF9faW5pdF9fKHNlbGYpIC0+IE5vbmU6CiAgICAgICAgc2VsZi5fbmFtZV93aWRnZXQ6IE9wdGlvbmFsW2JhLldpZGdldF0gPSBOb25lCiAgICAgICAgc2VsZi5fc2l6ZV93aWRnZXQ6IE9wdGlvbmFsW2JhLldpZGdldF0gPSBOb25lCiAgICAgICAgc2VsZi5fcGluZ193aWRnZXQ6IE9wdGlvbmFsW2JhLldpZGdldF0gPSBOb25lCiAgICAgICAgc2VsZi5fc3RhdHNfYnV0dG9uOiBPcHRpb25hbFtiYS5XaWRnZXRdID0gTm9uZQogICAgICAgIHNlbGYuX2lwX2J1dHRvbjpPcHRpb25hbFtiYS5XaWRnZXRdID0gTm9uZQogICAgZGVmIF9fZGVsX18oc2VsZikgLT4gTm9uZToKICAgICAgICBzZWxmLl9jbGVhcigpCgogICAgZGVmIF9jbGVhcihzZWxmKSAtPiBOb25lOgogICAgICAgIGZvciB3aWRnZXQgaW4gWwogICAgICAgICAgICAgICAgc2VsZi5fbmFtZV93aWRnZXQsIHNlbGYuX3NpemVfd2lkZ2V0LCBzZWxmLl9waW5nX3dpZGdldCwKICAgICAgICAgICAgICAgIHNlbGYuX3N0YXRzX2J1dHRvbiAsIHNlbGYuX2lwX2J1dHRvbgogICAgICAgIF06CiAgICAgICAgICAgIGlmIHdpZGdldDoKICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICB3aWRnZXQuZGVsZXRlKCkKICAgICAgICAgICAgICAgIGV4Y2VwdDoKICAgICAgICAgICAgICAgICAgICBwYXNzCiAgICBkZWYgaXB2aWV3KHNlbGYsY29sdW1ud2lkZ2V0LHBhcnR5KSAtPiBOb25lOgogICAgCWJhLnNjcmVlbm1lc3NhZ2UoIklQIFBPUlQgUmV2ZWFsZXIgYnkgTXIuU21vb3RoeSIpCiAgICAJQ29uZmlybVdpbmRvdyh0ZXh0PXN0cihwYXJ0eS5uYW1lKSsiXG4iKyJJUDogIitzdHIocGFydHkuYWRkcmVzcykrIiBQT1JUOiAiK3N0cihwYXJ0eS5wb3J0KSsiXG4iKyJTaXplIDogIitzdHIocGFydHkuc2l6ZSkrIi8iK3N0cihwYXJ0eS5zaXplX21heCkrIlxuIFF1ZXVlIElEOlxuIitzdHIocGFydHkucXVldWUpKyJcbiBcblBsdWdpbiBieTogTXIuU21vb3RoeSM1ODI0IiwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgYWN0aW9uPU5vbmUsd2lkdGg9NjAwLGhlaWdodD0yNTAsIGNhbmNlbF9idXR0b249RmFsc2UsIGNhbmNlbF9pc19zZWxlY3RlZD1GYWxzZSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgY29sb3I9KDAuOSwwLjksMC45KSwgdGV4dF9zY2FsZT0yLjAsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIG9yaWdpbl93aWRnZXQ9Y29sdW1ud2lkZ2V0KQogICAgZGVmIHVwZGF0ZShzZWxmLCBpbmRleDogaW50LCBwYXJ0eTogUGFydHlFbnRyeSwgc3ViX3Njcm9sbF93aWR0aDogZmxvYXQsCiAgICAgICAgICAgICAgIHN1Yl9zY3JvbGxfaGVpZ2h0OiBmbG9hdCwgbGluZWhlaWdodDogZmxvYXQsCiAgICAgICAgICAgICAgIGNvbHVtbndpZGdldDogYmEuV2lkZ2V0LCBqb2luX3RleHQ6IGJhLldpZGdldCwKICAgICAgICAgICAgICAgZmlsdGVyX3RleHQ6IGJhLldpZGdldCwgZXhpc3Rpbmdfc2VsZWN0aW9uOiBPcHRpb25hbFtTZWxlY3Rpb25dLAogICAgICAgICAgICAgICB0YWI6IFB1YmxpY0dhdGhlclRhYikgLT4gTm9uZToKICAgICAgICAiIiJVcGRhdGUgZm9yIHRoZSBnaXZlbiBkYXRhLiIiIgogICAgICAgICMgcHlsaW50OiBkaXNhYmxlPXRvby1tYW55LWxvY2FscwoKICAgICAgICAjIFF1aWNrLW91dDogaWYgd2UndmUgYmVlbiBtYXJrZWQgY2xlYW4gZm9yIGEgY2VydGFpbiBpbmRleCBhbmQKICAgICAgICAjIHdlJ3JlIHN0aWxsIGF0IHRoYXQgaW5kZXgsIHdlJ3JlIGRvbmUuCiAgICAgICAgaWYgcGFydHkuY2xlYW5fZGlzcGxheV9pbmRleCA9PSBpbmRleDoKICAgICAgICAgICAgcmV0dXJuCgogICAgICAgIHBpbmdfZ29vZCA9IF9iYS5nZXRfYWNjb3VudF9taXNjX3JlYWRfdmFsKCdwaW5nR29vZCcsIDEwMCkKICAgICAgICBwaW5nX21lZCA9IF9iYS5nZXRfYWNjb3VudF9taXNjX3JlYWRfdmFsKCdwaW5nTWVkJywgNTAwKQoKICAgICAgICBzZWxmLl9jbGVhcigpCiAgICAgICAgaHBvcyA9IDIwCiAgICAgICAgdnBvcyA9IHN1Yl9zY3JvbGxfaGVpZ2h0IC0gbGluZWhlaWdodCAqIGluZGV4IC0gNTAKICAgICAgICBzZWxmLl9uYW1lX3dpZGdldCA9IGJhLnRleHR3aWRnZXQoCiAgICAgICAgICAgIHRleHQ9YmEuTHN0cih2YWx1ZT1wYXJ0eS5uYW1lKSwKICAgICAgICAgICAgcGFyZW50PWNvbHVtbndpZGdldCwKICAgICAgICAgICAgc2l6ZT0oc3ViX3Njcm9sbF93aWR0aCAqIDAuNjMsIDIwKSwKICAgICAgICAgICAgcG9zaXRpb249KDAgKyBocG9zLCA0ICsgdnBvcyksCiAgICAgICAgICAgIHNlbGVjdGFibGU9VHJ1ZSwKICAgICAgICAgICAgb25fc2VsZWN0X2NhbGw9YmEuV2Vha0NhbGwoCiAgICAgICAgICAgICAgICB0YWIuc2V0X3B1YmxpY19wYXJ0eV9zZWxlY3Rpb24sCiAgICAgICAgICAgICAgICBTZWxlY3Rpb24ocGFydHkuZ2V0X2tleSgpLCBTZWxlY3Rpb25Db21wb25lbnQuTkFNRSkpLAogICAgICAgICAgICBvbl9hY3RpdmF0ZV9jYWxsPWJhLldlYWtDYWxsKHRhYi5vbl9wdWJsaWNfcGFydHlfYWN0aXZhdGUsIHBhcnR5KSwKICAgICAgICAgICAgY2xpY2tfYWN0aXZhdGU9VHJ1ZSwKICAgICAgICAgICAgbWF4d2lkdGg9c3ViX3Njcm9sbF93aWR0aCAqIDAuNDUsCiAgICAgICAgICAgIGNvcm5lcl9zY2FsZT0xLjQsCiAgICAgICAgICAgIGF1dG9zZWxlY3Q9VHJ1ZSwKICAgICAgICAgICAgY29sb3I9KDEsIDEsIDEsIDAuMyBpZiBwYXJ0eS5waW5nIGlzIE5vbmUgZWxzZSAxLjApLAogICAgICAgICAgICBoX2FsaWduPSdsZWZ0JywKICAgICAgICAgICAgdl9hbGlnbj0nY2VudGVyJykKICAgICAgICBiYS53aWRnZXQoZWRpdD1zZWxmLl9uYW1lX3dpZGdldCwKICAgICAgICAgICAgICAgICAgbGVmdF93aWRnZXQ9am9pbl90ZXh0LAogICAgICAgICAgICAgICAgICBzaG93X2J1ZmZlcl90b3A9NjQuMCwKICAgICAgICAgICAgICAgICAgc2hvd19idWZmZXJfYm90dG9tPTY0LjApCiAgICAgICAgaWYgZXhpc3Rpbmdfc2VsZWN0aW9uID09IFNlbGVjdGlvbihwYXJ0eS5nZXRfa2V5KCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBTZWxlY3Rpb25Db21wb25lbnQuTkFNRSk6CiAgICAgICAgICAgIGJhLmNvbnRhaW5lcndpZGdldChlZGl0PWNvbHVtbndpZGdldCwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHNlbGVjdGVkX2NoaWxkPXNlbGYuX25hbWVfd2lkZ2V0KQogICAgICAgIGlmIHBhcnR5LnN0YXRzX2FkZHI6CiAgICAgICAgICAgIHVybCA9IHBhcnR5LnN0YXRzX2FkZHIucmVwbGFjZSgKICAgICAgICAgICAgICAgICcke0FDQ09VTlR9JywKICAgICAgICAgICAgICAgIF9iYS5nZXRfYWNjb3VudF9taXNjX3JlYWRfdmFsXzIoJ3Jlc29sdmVkQWNjb3VudElEJywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgJ1VOS05PV04nKSkKICAgICAgICAgICAgc2VsZi5fc3RhdHNfYnV0dG9uID0gYmEuYnV0dG9ud2lkZ2V0KAogICAgICAgICAgICAgICAgY29sb3I9KDAuMywgMC42LCAwLjk0KSwKICAgICAgICAgICAgICAgIHRleHRjb2xvcj0oMS4wLCAxLjAsIDEuMCksCiAgICAgICAgICAgICAgICBsYWJlbD1zdHIoInN0YXRzIiksCiAgICAgICAgICAgICAgICBwYXJlbnQ9Y29sdW1ud2lkZ2V0LAogICAgICAgICAgICAgICAgYXV0b3NlbGVjdD1UcnVlLAogICAgICAgICAgICAgICAgb25fYWN0aXZhdGVfY2FsbD1iYS5DYWxsKGJhLm9wZW5fdXJsLCB1cmwpLAogICAgICAgICAgICAgICAgb25fc2VsZWN0X2NhbGw9YmEuV2Vha0NhbGwoCiAgICAgICAgICAgICAgICAgICAgdGFiLnNldF9wdWJsaWNfcGFydHlfc2VsZWN0aW9uLAogICAgICAgICAgICAgICAgICAgIFNlbGVjdGlvbihwYXJ0eS5nZXRfa2V5KCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIFNlbGVjdGlvbkNvbXBvbmVudC5TVEFUU19CVVRUT04pKSwKICAgICAgICAgICAgICAgIHNpemU9KDgwLCAzMCksCiAgICAgICAgICAgICAgICBwb3NpdGlvbj0oc3ViX3Njcm9sbF93aWR0aCAqIDAuNzAgKyBocG9zLCAxMCArIHZwb3MpLAogICAgICAgICAgICAgICAgc2NhbGU9MC43KQogICAgICAgICAgICBpZiBleGlzdGluZ19zZWxlY3Rpb24gPT0gU2VsZWN0aW9uKAogICAgICAgICAgICAgICAgICAgIHBhcnR5LmdldF9rZXkoKSwgU2VsZWN0aW9uQ29tcG9uZW50LlNUQVRTX0JVVFRPTik6CiAgICAgICAgICAgICAgICBiYS5jb250YWluZXJ3aWRnZXQoZWRpdD1jb2x1bW53aWRnZXQsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgc2VsZWN0ZWRfY2hpbGQ9c2VsZi5fc3RhdHNfYnV0dG9uKQogICAgICAgIHNlbGYuX2lwX2J1dHRvbiA9IGJhLmJ1dHRvbndpZGdldCgKICAgICAgICAgICAgICAgIGNvbG9yPSgwLjksIDAuMywgMC4yNCksCiAgICAgICAgICAgICAgICB0ZXh0Y29sb3I9KDEuMCwgMS4wLCAxLjApLAogICAgICAgICAgICAgICAgbGFiZWw9c3RyKCJJUCIpLAogICAgICAgICAgICAgICAgcGFyZW50PWNvbHVtbndpZGdldCwKICAgICAgICAgICAgICAgIGF1dG9zZWxlY3Q9VHJ1ZSwKICAgICAgICAgICAgICAgIG9uX2FjdGl2YXRlX2NhbGw9YmEuQ2FsbChzZWxmLmlwdmlldyxjb2x1bW53aWRnZXQscGFydHkpLAogICAgICAgICAgICAgICAgb25fc2VsZWN0X2NhbGw9YmEuV2Vha0NhbGwoCiAgICAgICAgICAgICAgICAgICAgdGFiLnNldF9wdWJsaWNfcGFydHlfc2VsZWN0aW9uLAogICAgICAgICAgICAgICAgICAgIFNlbGVjdGlvbihwYXJ0eS5nZXRfa2V5KCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIFNlbGVjdGlvbkNvbXBvbmVudC5TVEFUU19CVVRUT04pKSwKICAgICAgICAgICAgICAgIHNpemU9KDU5LCAzMCksCiAgICAgICAgICAgICAgICBwb3NpdGlvbj0oc3ViX3Njcm9sbF93aWR0aCAqIDAuNjQgKyBocG9zLCAxMCArIHZwb3MpLAogICAgICAgICAgICAgICAgc2NhbGU9MC43KQoKICAgICAgICBzZWxmLl9zaXplX3dpZGdldCA9IGJhLnRleHR3aWRnZXQoCiAgICAgICAgICAgIHRleHQ9c3RyKHBhcnR5LnNpemUpICsgJy8nICsgc3RyKHBhcnR5LnNpemVfbWF4KSwKICAgICAgICAgICAgcGFyZW50PWNvbHVtbndpZGdldCwKICAgICAgICAgICAgc2l6ZT0oMCwgMCksCiAgICAgICAgICAgIHBvc2l0aW9uPShzdWJfc2Nyb2xsX3dpZHRoICogMC44NiArIGhwb3MsIDIwICsgdnBvcyksCiAgICAgICAgICAgIHNjYWxlPTAuNywKICAgICAgICAgICAgY29sb3I9KDAuOCwgMC44LCAwLjgpLAogICAgICAgICAgICBoX2FsaWduPSdyaWdodCcsCiAgICAgICAgICAgIHZfYWxpZ249J2NlbnRlcicpCgogICAgICAgIGlmIGluZGV4ID09IDA6CiAgICAgICAgICAgIGJhLndpZGdldChlZGl0PXNlbGYuX25hbWVfd2lkZ2V0LCB1cF93aWRnZXQ9ZmlsdGVyX3RleHQpCiAgICAgICAgICAgIGlmIHNlbGYuX3N0YXRzX2J1dHRvbjoKICAgICAgICAgICAgICAgIGJhLndpZGdldChlZGl0PXNlbGYuX3N0YXRzX2J1dHRvbiwgdXBfd2lkZ2V0PWZpbHRlcl90ZXh0KQoKICAgICAgICBzZWxmLl9waW5nX3dpZGdldCA9IGJhLnRleHR3aWRnZXQocGFyZW50PWNvbHVtbndpZGdldCwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgc2l6ZT0oMCwgMCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHBvc2l0aW9uPShzdWJfc2Nyb2xsX3dpZHRoICogMC45NCArCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBocG9zLCAyMCArIHZwb3MpLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBzY2FsZT0wLjcsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGhfYWxpZ249J3JpZ2h0JywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgdl9hbGlnbj0nY2VudGVyJykKICAgICAgICBpZiBwYXJ0eS5waW5nIGlzIE5vbmU6CiAgICAgICAgICAgIGJhLnRleHR3aWRnZXQoZWRpdD1zZWxmLl9waW5nX3dpZGdldCwKICAgICAgICAgICAgICAgICAgICAgICAgICB0ZXh0PSctJywKICAgICAgICAgICAgICAgICAgICAgICAgICBjb2xvcj0oMC41LCAwLjUsIDAuNSkpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgYmEudGV4dHdpZGdldChlZGl0PXNlbGYuX3Bpbmdfd2lkZ2V0LAogICAgICAgICAgICAgICAgICAgICAgICAgIHRleHQ9c3RyKGludChwYXJ0eS5waW5nKSksCiAgICAgICAgICAgICAgICAgICAgICAgICAgY29sb3I9KDAsIDEsIDApIGlmIHBhcnR5LnBpbmcgPD0gcGluZ19nb29kIGVsc2UKICAgICAgICAgICAgICAgICAgICAgICAgICAoMSwgMSwgMCkgaWYgcGFydHkucGluZyA8PSBwaW5nX21lZCBlbHNlICgxLCAwLCAwKSkKCiAgICAgICAgcGFydHkuY2xlYW5fZGlzcGxheV9pbmRleCA9IGluZGV4CgpkZWYgZnVja2trKCk6CgliYXN0ZF91aV9nYXRoZXIucHVibGljdGFiLlVJUm93PSBuZXdVSVJvdw==").decode("ascii"))
# ba_meta export plugin
class enablee(ba.Plugin):
    def __init__(self):
        if _ba.env().get("build_number",0) >= 20258:
            fuckkk()
        else:print("IPPORT REVEALER works with BombSquad version higer than 1.5.29.")