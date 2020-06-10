package com.u8.sdk.qh360.wxapi;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.Window;

import com.qihoo.gamecenter.sdk.matrix.Matrix;
import com.qihoo.gamecenter.sdk.protocols.ProtocolConfigs;
import com.qihoo.gamecenter.sdk.protocols.ProtocolKeys;

public class WXEntryActivity extends Activity {

    public void onCreate(Bundle savedInstanceState) {
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        requestWindowFeature(Window.FEATURE_PROGRESS);
        super.onCreate(savedInstanceState);
        Intent intent = getIntent();
        try {
        	Matrix.wxLoginCallback(getIntent());
            intent.getStringExtra("try");
            intent.putExtra(ProtocolKeys.FUNCTION_CODE, ProtocolConfigs.FUNC_CODE_HANDEL_WEIXIN_CALLBACK);
            Matrix.execute(this, intent, null);
        } catch (Throwable tr) {
            finish();
            return;
        }
        finish();
    }
    
    @Override
    protected void onNewIntent(Intent intent) {
    	super.onNewIntent(intent);
    	try {
    		Matrix.wxLoginCallback(getIntent());
		} catch (Exception e) {
		}
    	finish();
    }

}
