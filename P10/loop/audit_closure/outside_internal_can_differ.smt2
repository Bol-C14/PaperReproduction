; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let (($x88 (and (distinct (bvadd (bvmul a b) c) (bvadd (bvmul ((_ zero_extend 13) ((_ extract 2 0) a)) b) c)) true)))
(and (not (bvult a (_ bv8 16))) $x88)))
(check-sat)
