# Solana Blockpit Reference Exclusions - 2026-05-09

## Zweck

Exakte Blockpit-Solana-Referenzzeilen ausschliessen, wenn dieselbe On-Chain-Bewegung bereits aus Solana-RPC als Primaerdatensatz vorhanden ist.

- Modus: `execute`
- Exact Matches: `1875`
- Import Result: `{'excluded_event_count': 1875, 'unchanged_exclusions': 0, 'alias_inserted_or_updated': 2}`

## Alias Upserts

- `7ATGF8KQO4WJRD5ATGX7T1V2ZVVYKPJBFFNEVF1ICFV1` -> `CWIF` (catwifhat)
- `2KFZCKFXJ1US8YRQZA5VKTSXY3GPZFZVVHWJ91N8FV2J` -> `CBDC` (CBDC)

## Beispiele

- `2024-01-12T05:00:21+00:00` `IOT` `5624.359439` `in` tx `9FyqjZU1CFrQPsVTvXoJmJzJWo41BQcsVUrYJFjVPfA5ZnJWyaV6LHB5xmurMx8G69CM74xuNED77mM5eSYQkjD` blockpit `e4a52904ba70f656ea8d9ac88f201d216b405790b7b1394298dad576bd793b04` rpc `852a40037f011c5f1fa84a9fa88b3adfee7f99b1c745c0994d9dde194eea2c99`
- `2024-01-12T05:00:21+00:00` `SOL` `0.00001` `out` tx `9FyqjZU1CFrQPsVTvXoJmJzJWo41BQcsVUrYJFjVPfA5ZnJWyaV6LHB5xmurMx8G69CM74xuNED77mM5eSYQkjD` blockpit `ce05ff0bd130364ec9fdbab6ce03a824bb951ade072b1b6827778114c29eca4f` rpc `354ac3633447a8866d83e5fb8d814f54bea563d66a2bd0525f230963257e4506`
- `2024-01-12T05:00:22+00:00` `IOT` `8725.36255` `in` tx `53TpbXeJpx4qenG19vefu6ARh1CoUVYos3Jrm5anay8EftW7Xd7QYAxTyuwWhrgcsG1B7WWbmm4PrtTJLGy2XdTK` blockpit `9159d2a7ae61e89eadec290ec18b1fe3b169a86b4b3636ab43596d879022cbb8` rpc `45d89f5cc093db53dbae750130b08dd19445e6b29ffcfe5c13acf3bf4447f848`
- `2024-01-12T05:00:22+00:00` `IOT` `8087.388577` `in` tx `NwYCo1TjeQkCHhYLqdP1bE6ZAUx5XY3U5fbszynwnpzwgCaJLxBtXxDybi8gEtBRAjvNHxhgV9r7iLarLr96RRB` blockpit `6c611e5dbbe2ee4778ad7fad9aa5ec73d3676ae3e9887ca9a027aa3d5494169b` rpc `87efbd3803b35f11f736f2a20c6fb0b21dc7cbd90bba74481cc7bf7bee38e01f`
- `2024-01-12T05:00:22+00:00` `SOL` `0.00001` `out` tx `53TpbXeJpx4qenG19vefu6ARh1CoUVYos3Jrm5anay8EftW7Xd7QYAxTyuwWhrgcsG1B7WWbmm4PrtTJLGy2XdTK` blockpit `6ea04421dd5b6bf76913c01b86642ce91231ccfed4ae1034d3bc9805a4d59ce1` rpc `3f7e57013034012b9bccdd23c96ca23d870e18d185ccbf3c78f3d2815ea7c0fb`
- `2024-01-12T05:00:22+00:00` `SOL` `0.00001` `out` tx `NwYCo1TjeQkCHhYLqdP1bE6ZAUx5XY3U5fbszynwnpzwgCaJLxBtXxDybi8gEtBRAjvNHxhgV9r7iLarLr96RRB` blockpit `12964822d927ee9c82cc5da3fa0eafd9667d0e664c60f6a44511f414cc4996a5` rpc `86f11c04fb45ca986920652b8e1e0707d2e1cb26e48e8475776185e684e8bcb7`
- `2024-01-12T05:00:24+00:00` `IOT` `21051.202845` `in` tx `cAqnYhmTarFW5t5zWZLeGBK2g3PKmaRQxir3nVvZgEXaj3ifqF1BQN97NmjkKjZFsYYzT2UnGAV9jotGgtLpU7s` blockpit `56b373c22f98df0c2cae77a1addb3e3e63738f46f31e5e11ead60f66ceec1e4f` rpc `80cb7643b8ee1fda2ba8dbd2a1af0371eafe4b63add2145a8d48fcd0abb4fb96`
- `2024-01-12T05:00:24+00:00` `SOL` `0.00001` `out` tx `cAqnYhmTarFW5t5zWZLeGBK2g3PKmaRQxir3nVvZgEXaj3ifqF1BQN97NmjkKjZFsYYzT2UnGAV9jotGgtLpU7s` blockpit `6542d8849c8c0b6db2a12c7e6f6c14ff148ad624fcf7556563a0424581bb100c` rpc `ab9b2d5cf5a4225f489719ef3116b5b7fd16fd1ae785e10965f8123523912501`
- `2024-01-12T05:00:28+00:00` `IOT` `11218.621122` `in` tx `nq57J1M5v1vY8duUGrRdhSFDN1RbxSKPyjSaPjcBiiT7KJdfaYkCVM2VrPwoFNw6ET46Ewi35XCJ38q4XM5H1bE` blockpit `27d8b35207ec39a706f5117889fec07cc9d626e263899c25d8b1150ebd60eb70` rpc `9b543fe9edf471db9124f9f8d23b4ca5c0a0aa3ab07c1a8102f2b77f7ad06b2b`
- `2024-01-12T05:00:28+00:00` `SOL` `0.00001` `out` tx `nq57J1M5v1vY8duUGrRdhSFDN1RbxSKPyjSaPjcBiiT7KJdfaYkCVM2VrPwoFNw6ET46Ewi35XCJ38q4XM5H1bE` blockpit `0f841c256600ca69c8aee4309cdd71422594e86673c9f62a654c73284a960d31` rpc `74e7bba1ce9efcc5d56097aaffb7156f875dd56bf17f43b1358a8b2fab651a76`
- `2024-01-12T05:00:31+00:00` `IOT` `9629.503834` `in` tx `5mncWWki84YHGqgKnbSkzmGx3KvXnbRaVY8Xw4tNaAwgHPjx7qBjSQfNqErdtDiE72uCnpj9sha4hf4bnzmekGov` blockpit `1319e230e74c519831edcadd7c06bc32dd753255fc101c095ef1a94c26a9d9ab` rpc `5dbbddee237ff15189b56e2fcad1e946f71e1a627aa9e6b1f0b75340a2a4d569`
- `2024-01-12T05:00:31+00:00` `SOL` `0.00001` `out` tx `5mncWWki84YHGqgKnbSkzmGx3KvXnbRaVY8Xw4tNaAwgHPjx7qBjSQfNqErdtDiE72uCnpj9sha4hf4bnzmekGov` blockpit `4a8d6a424e3a7add9050ee063dcb08caf27fabd5ffdb4fed53be522de6931ae6` rpc `f513ac6ed09bece25fdf26597bcac088de69f68368d27b4717cf75c8159d3e7c`
- `2024-01-12T05:00:37+00:00` `IOT` `7984.738099` `in` tx `5Gi5W71TPZJ1Z6JLoBPiECm6iXYQQRm22djNRBnE1HejfymgS1QgGJpb3FGq5o33RGZ7CuntBN6MXcPFthez1BsZ` blockpit `88f54ab731fb91f4c1fef327d1120cd5db7eba1f983ac7dbac2af57ec7740bc2` rpc `4bf6848fc56a02f98fd87b68d0389aa8a2e4be8fea1b89ad37b9664bf0b7fc1c`
- `2024-01-12T05:00:37+00:00` `SOL` `0.00001` `out` tx `5Gi5W71TPZJ1Z6JLoBPiECm6iXYQQRm22djNRBnE1HejfymgS1QgGJpb3FGq5o33RGZ7CuntBN6MXcPFthez1BsZ` blockpit `a5c6be00b548865faa17440664edfdf3a4d744782e21f73a1d6eb9962218545a` rpc `7db210b2e9ddbf970c9a0d1b6009549a58dd3c582f67fe5c6d990976f2f3cf34`
- `2024-01-12T05:00:39+00:00` `IOT` `6868.820496` `in` tx `5kzYY8vs1aFdCXT1ZJuCViXoBCuB88VRFFKBhDTNQB7oNR6ybVp6UX7mDqTW6csP5Ct8pnQEr1th8SRTjNXsFnLN` blockpit `3e70f1e08bc142397ca782dda98a57a32857382f50f868355f5cb7fce16159ad` rpc `89c581c31b9da2dace3fe0a2db4482c389627d6b5541270ec286d813c3dbe3e6`
- `2024-01-12T05:00:39+00:00` `SOL` `0.00001` `out` tx `5kzYY8vs1aFdCXT1ZJuCViXoBCuB88VRFFKBhDTNQB7oNR6ybVp6UX7mDqTW6csP5Ct8pnQEr1th8SRTjNXsFnLN` blockpit `46cf66df3e0c3ca9321de86b66888654fe99ef699fb5b8a2e0c38b54a3a604e6` rpc `0fa6531ce950193b0c7df6a03b104b80117a345ba451c40247963ee16997c0af`
- `2024-01-12T05:02:48+00:00` `IOT` `75E+3` `out` tx `4cLjCQ7kQWBcoY16Kjv7FtaN8oQyt346ZzymDPc4Vznz116RMXwYX2P67Q6tSTPwdeJiTjcmieBXJk6YqCFJdxck` blockpit `e13eac1ccab1b33b08591f23bfdd9775e94bfc5e23ab625f6c0ede9aba1b65ba` rpc `2725e9ea8a6b029f11ee02fdde0c61af0827b72d17e48a9bb322e60717f5f414`
- `2024-01-12T05:06:20+00:00` `SOL` `0.000005` `in` tx `eMb5WT3he1oiBbcTdtpvwfAXg4BDQBjH3rWt725Qc5QUmYWACMXsWn4crsYGTLmzZkZVV3Mgqt4qacqW6TQw76q` blockpit `09532a0b3e4ee759f521b8a8771f9b3e5f906f9bc38fa505b6f36a7b0b371b6d` rpc `ba72f0f9d119d4d9c5d5d2837f199d68333f5af87ae61878606f458309764ac0`
- `2024-01-17T18:09:05+00:00` `SOL` `0.000005` `out` tx `2mGRQcLDzFiVE5LHV8crmBG8QpEBqetWVbq8Rb3sNmGBBMkLCjn8H2dEuCjc29jspKMYF19q5kzrwheWWnruR4Q6` blockpit `c1c993811a3f668d89cfb189dac9edf89ee7ed4061cfc8af1a33a57455486da2` rpc `d127db510a2ea3f31411c58c2e82e5bd6639b59fc35014f4c17f3a4029a98be5`
- `2024-01-18T01:28:25+00:00` `IOT` `164.879512` `in` tx `2mLGmw6rAtFmQyjqXT6kEdon3fJLNFhTpDEfWg5XM7g8RNeocsvnfyJkQ1Cvt71NMcaDwsFjyDUXGpNpJ9HiZ4MC` blockpit `e64e2cee33cef5ce0626ecc6ce280cb3795c3ec576942ee7f3efe1043ca35cf0` rpc `dc4e3205e4bd57d560023aea3f704de5c964b9a911e326880bc72c5182f70ffc`
- `2024-01-18T01:28:25+00:00` `SOL` `0.000005001` `out` tx `2mLGmw6rAtFmQyjqXT6kEdon3fJLNFhTpDEfWg5XM7g8RNeocsvnfyJkQ1Cvt71NMcaDwsFjyDUXGpNpJ9HiZ4MC` blockpit `49fd0e7a7cd9ce6106b3b0b5a27c6c2734fbf7bfadfc2f151e0fb5774ed21171` rpc `035f6f8cea94a4baf5f18aec0c452c2886d4afd113beb1a657d74c90f2db08de`
- `2024-01-18T01:28:27+00:00` `IOT` `295.986167` `in` tx `4kAvxvwm1aCzxKviAymmwgpkF28tkTdhd7JRNk1kQ8XkUwY64GbB7wqCZaFpRXsiRgWfwEctKKKJ5SNucBezX4dH` blockpit `25591a219c174d8addd38d50d93fd37a2f0267eb2725b53e1f83bc32066a1f3d` rpc `664124eb86ad15746d6be581a9096b67a640a2c0882c117cf907bc959b989f0c`
- `2024-01-18T01:28:27+00:00` `SOL` `0.000005001` `out` tx `4kAvxvwm1aCzxKviAymmwgpkF28tkTdhd7JRNk1kQ8XkUwY64GbB7wqCZaFpRXsiRgWfwEctKKKJ5SNucBezX4dH` blockpit `b8dffc378e11d13e467ad0c6d5bed0d0ca14afbd54af1cb382844d836eab6c86` rpc `23566fd42b4d4adf96fe930cbda444bcac4af49354b1a4e7280c6ec1138715a4`
- `2024-01-18T01:28:38+00:00` `IOT` `295.867952` `in` tx `4MQDtzdN6fPEXVKghi8MigfRctKt9gwZkECRVnYto8ptvaRXZ21DQ2qzcPAhrSpSVFaa9gvyKRzQg5YBVAWgefzn` blockpit `089e9d9dd05597fcdeff528546f5b05a55808ba004d8b45684e3566741083e2e` rpc `c9b285ce869b65770336aeff29b5cebe71f4427a0b8a883f17b93f5ea9ad65e5`
- `2024-01-18T01:28:38+00:00` `SOL` `0.000005001` `out` tx `4MQDtzdN6fPEXVKghi8MigfRctKt9gwZkECRVnYto8ptvaRXZ21DQ2qzcPAhrSpSVFaa9gvyKRzQg5YBVAWgefzn` blockpit `6bb56941a3962193c14c1d8f27da064d65978665e67753831b24a21ec283ba0e` rpc `369329d5603b62e7ea8c94fb94dca5761b9d4a361dc497a7de0c108e877aabb9`

## Bewertung

- Only exact matches are used: tx_id, canonical asset, side, quantity and timestamp must align.
- Solana RPC is treated as primary on-chain evidence; Blockpit Solana rows are retained as RAW evidence but excluded tax-effectively.
- Alias upserts are limited to mints that match Blockpit symbols on the same Solana transaction and amount.
